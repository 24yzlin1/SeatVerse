# SeatVerse · 主办方名单与票务写入契约（F）

> 状态：实现已落地，待 A 合并进 `docs/contracts/api.md` ｜ 负责人：F ｜ 日期：2026-11-17
> 适用：主办方名单页、核验页，以及 E 的预约事务
> 依据：`api.md §3` #14—#17、`ticket-qr.md §4.2`、05 号《分工方案》§四“F → E 内部能力”

`api.md` 已冻结 `Ticket` 形状（§4.3）与四个票务接口的路径、权限，但
`GET /events/{id}/bookings` 的 `payload` 形状、写票函数的调用约定尚未成文。
本文补齐这两处，字段口径与既有契约一致。

---

## 1. `GET /api/events/{id}/bookings`

### 1.1 权限

| 情况 | 结果 |
|---|---|
| 未登录 | `401` |
| 已登录但不是 `organizer` | `403` |
| 活动不存在 / 不是自己的活动 | `404`，文案 `活动不存在或无权查看` |
| 本人活动 | `200` + 分页名单 |

### 1.2 查询参数

| 参数 | 类型 | 默认 | 约束 |
|---|---|---|---|
| `page` | integer | `1` | `>= 1`，否则 `400` |
| `pageSize` | integer | `20` | `1—100`，否则 `400` |

### 1.3 响应 `payload`（`Page<RosterEntry>`）

```json
{
  "items": [
    {
      "id": 9001,
      "status": "reserved",
      "createdAt": "2026-11-17T20:00:00+08:00",
      "cancelledAt": null,
      "ticketCode": "SV7F3K9Q2M4T8X6B5N2P",
      "user": { "id": 3, "name": "用户甲", "email": "user-one@example.com" },
      "seats": [
        { "id": 11, "row": 1, "number": 1, "label": "1排1号", "seatType": "standard" }
      ],
      "verifiedAt": null,
      "verifiedBy": null
    }
  ],
  "total": 3,
  "page": 1,
  "pageSize": 20
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer | 预约编号（不是票号） |
| `status` | `reserved` / `cancelled` / `used` | `bookings.status` 原值，不做展示态派生 |
| `createdAt` / `cancelledAt` | string / null | ISO 8601；未取消时 `cancelledAt` 为 `null` |
| `ticketCode` | string / null | 对应电子票票号；历史脏数据可能为 `null` |
| `user` | object | `id` / `name` / `email`，现场核对用 |
| `seats` | `SeatBrief[]` | 按 `row`、`number` 升序；已取消预约仍保留原座位 |
| `verifiedAt` / `verifiedBy` | string·null / integer·null | 未核验为 `null` |

约定：

1. 排序固定 `createdAt ASC, id ASC`（报名先后）。
2. **不做服务端状态分组**，也不接受 `status` 过滤；前端本地分组（与 `api.md §4.1` 分页口径一致）。
3. 只返回本活动的预约；已取消预约保留在名单中，票面由 `verifiedAt` 与 `status` 派生。

---

## 2. 票写函数（E 的预约事务调用）

票号在预约事务内生成并写入（`ticket-qr.md §2.2`）。F 提供：

```python
from app.repos.tickets import insert_ticket   # 只写 SQL，不 commit、不 close
from app.core.tickets import generate_ticket_code  # 20 位 Crockford Base32
```

| 约定 | 说明 |
|---|---|
| 传入连接 | `insert_ticket(connection, booking_id, ticket_code)` 使用调用方事务的连接 |
| 不自行提交 | 函数内没有 `commit` / `rollback`；由 E 的预约事务提交或回滚 |
| 返回类型 | `TicketRow(id, booking_id, ticket_code, verified_at, verified_by)` |
| 票号唯一 | `tickets.ticket_code` 唯一约束；重复抛 `sqlite3.IntegrityError`，由 E 重试生成 |
| 票号格式 | 一律走 `generate_ticket_code()`，禁止自增编号 / 时间戳 / 拼接 |
| 取消 | 不删票、不改票号；票面状态按 `enums.md §2.5` 派生为 `cancelled` |

E 当前实现（`app/core/bookings.py`）已在同一事务内调用 `insert_ticket`，与本节一致。

---

## 3. 核验规则（与 `ticket-qr.md §4.2` 一致）

| 检查顺序 | 条件 | 结果 |
|---|---|---|
| 1 | 未登录 | `401` |
| 2 | 非 `organizer` | `403` |
| 3 | 票号格式非法 / 不存在 / 不属于本主办方活动 | `404`（同文案） |
| 4 | 已核验 | `409`，`message` 含首次核验时间 |
| 5 | 预约已取消 | `409` |
| 6 | 活动已取消 | `409` |
| 7 | `now >= event.endTime` | `409` |
| 8 | 条件更新失败（并发抢核验） | `409` |

核验成功返回更新后的完整 `Ticket`（`status = "used"`、`verifiedAt` 非空），
`bookings.status` 同步改为 `used`；座位保持 `sold`。读票与核验在同一写事务内重查，
条件更新保证并发重复核验只有一个成功。

---

## 4. 验收清单

用例位于 `backend/tests/test_tickets.py`，2026-11-17 本地执行 **11 passed**。

| # | 用例 | 覆盖点 |
|---|---|---|
| 1 | 本人票查询、他人票与不存在同码同文案 | 防枚举、camelCase 字段、座位排序 |
| 2 | 票号归一化（小写 / 连字符）与格式非法 | `ticket-qr.md §2.3` |
| 3 | 核验成功、重复核验 `409` 且回显首次时间 | 条件更新 + 预约状态同步 |
| 4 | 角色不足 `403`、跨主办方 `404`、未登录 `401` | 权限矩阵 |
| 5 | 已取消预约 / 已取消活动 / 已结束活动不能签到 | 有效期规则 |
| 6 | 名单只给本活动主办方、分页与越界参数 | `page` / `pageSize` 校验 |
| 7 | 主办方建活动（草稿）、普通用户 `403`、非法时间 `400` | `POST /events` |
| 8 | `GET /events?pageSize=` 生效 | 分页参数别名 |

```bash
cd backend
uv run pytest -q
uv run mypy app scripts main.py
```

---

## 5. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-17 | 首版：补名单形状、写票函数约定、核验顺序与 8 组验收用例 | F |
