# SeatVerse 数据库字典（第一版）

> 负责人：E ｜ 对应建表脚本：`backend/app/repos/migrations/000_schema.sql`
> 数据库：SQLite 单文件（WAL 模式，外键开启，`busy_timeout=15000`）
> 时间字段统一为带时区偏移的 ISO 8601 字符串，例如 `2026-12-20T19:00:00+08:00`。

## 1. 表清单

| # | 表 | 用途 |
|---|---|---|
| 1 | `users` | 用户与角色（普通用户 / 主办方） |
| 2 | `venues` | 场馆；第一版只有 1 行 |
| 3 | `seats` | 场馆固定座位与 3D 坐标 |
| 4 | `events` | 活动信息与状态 |
| 5 | `event_seats` | 每场活动每个座位的动态状态 |
| 6 | `bookings` | 预约单 |
| 7 | `booking_seats` | 预约与座位的关联（含有效标记） |
| 8 | `tickets` | 电子票与核验记录 |

---

## 2. `users` 用户

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键（SQLite rowid 别名） |
| `name` | TEXT | 否 | — | 展示名 |
| `email` | TEXT | 否 | — | `COLLATE NOCASE UNIQUE`，大小写不敏感唯一 |
| `password_hash` | TEXT | 否 | — | scrypt 散列，不存明文 |
| `role` | TEXT | 否 | — | `CHECK (role IN ('user','organizer'))` |
| `created_at` | TEXT | 否 | — | 注册时间 ISO 8601 |

索引：`email` 唯一约束自带索引。

---

## 3. `venues` 场馆

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键 |
| `name` | TEXT | 否 | — | 场馆名 |
| `layout_config` | TEXT | 否 | `'{}'` | JSON 字符串；第一版为 `{"rows":10,"columns":12}` |
| `capacity` | INTEGER | 否 | — | 容量，种子为 120 |

> 第一版只写入 1 行，但表结构支持多场馆；代码禁止把场馆编号写死，必须查库。

---

## 4. `seats` 固定座位

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键；与 3D 的 `seatId` 对齐 |
| `venue_id` | INTEGER | 否 | — | FK → `venues.id` |
| `row_number` | INTEGER | 否 | — | 排号，从 1 开始 |
| `seat_number` | INTEGER | 否 | — | 座号，从 1 开始 |
| `x` | REAL | 否 | — | 3D 横坐标（米） |
| `y` | REAL | 否 | — | 3D 纵坐标（米） |
| `z` | REAL | 否 | — | 3D 纵深（米） |
| `seat_type` | TEXT | 否 | `'standard'` | `CHECK (seat_type IN ('standard'))` |

约束/索引：

- `UNIQUE (venue_id, row_number, seat_number)`：同场馆同排同座不能重复；
- `seat_type` 第一版只有 `standard`。

---

## 5. `events` 活动

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键 |
| `title` | TEXT | 否 | — | 活动标题 |
| `description` | TEXT | 否 | `''` | 简介 |
| `start_time` | TEXT | 否 | — | 开始时间 ISO 8601，含时区 |
| `end_time` | TEXT | 否 | — | 结束时间，必须晚于开始时间（业务校验） |
| `organizer_id` | INTEGER | 否 | — | FK → `users.id` |
| `venue_id` | INTEGER | 否 | — | FK → `venues.id` |
| `status` | TEXT | 否 | `'draft'` | `CHECK (status IN ('draft','published','closed','cancelled'))` |
| `created_at` | TEXT | 否 | — | 创建时间 |

状态语义：

| 值 | 含义 | 接受新预约 |
|---|---|---|
| `draft` | 草稿 | 否 |
| `published` | 已发布 | 是（且未开始、未结束） |
| `closed` | 已停止预约 | 否；已有预约仍可取消/核验 |
| `cancelled` | 活动取消 | 否；已有票不能核验 |

> “进行中/已结束”是按 `start_time` / `end_time` 派生的展示态，不写入 `status`。

---

## 6. `event_seats` 每场活动座位状态

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键 |
| `event_id` | INTEGER | 否 | — | FK → `events.id` |
| `seat_id` | INTEGER | 否 | — | FK → `seats.id` |
| `status` | TEXT | 否 | `'available'` | `CHECK (status IN ('available','locked','sold'))` |
| `version` | INTEGER | 否 | `0` | 并发控制版本号；每次条件更新 `+1` |

约束/索引：

- `UNIQUE (event_id, seat_id)`：同一场活动同一座位只能有一行状态；
- `ix_event_seats_event(event_id, status)`：按活动筛选状态。

状态语义：

- `available`：可预约；
- `sold`：已被有效预约占用；
- `locked`：预留枚举，第一版不写入。

> 发布活动时由 D 的发布事务调用 E 的 `initialize_event_seats`，按 `seats` 批量生成 `available` 行；草稿不生成。

---

## 7. `bookings` 预约单

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键 |
| `event_id` | INTEGER | 否 | — | FK → `events.id` |
| `user_id` | INTEGER | 否 | — | FK → `users.id` |
| `status` | TEXT | 否 | `'reserved'` | `CHECK (status IN ('reserved','cancelled','used'))` |
| `created_at` | TEXT | 否 | — | 下单时间 |
| `cancelled_at` | TEXT | 是 | `NULL` | 取消时间；未取消为 NULL |

索引：

- `ix_bookings_user(user_id, created_at DESC, id DESC)`：我的预约按时间倒序分页。

状态语义：

- `reserved`：待参加；
- `cancelled`：已取消；
- `used`：已核验签到。

---

## 8. `booking_seats` 预约座位关联

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键 |
| `booking_id` | INTEGER | 否 | — | FK → `bookings.id` |
| `event_id` | INTEGER | 否 | — | FK → `events.id` |
| `seat_id` | INTEGER | 否 | — | FK → `seats.id` |
| `is_active` | INTEGER | 否 | `1` | `CHECK (is_active IN (0,1))`；0/1 映射 Python `bool` |

关键约束：

```sql
CREATE UNIQUE INDEX ux_booking_seats_active
  ON booking_seats (event_id, seat_id) WHERE is_active = 1;
```

- 有效占用（`is_active=1`）同一活动同一座位只允许一条；
- 取消后置 `0`，历史行保留，允许同一座位被重新预约；
- “我的预约”显示座位时**不能加** `is_active=1` 过滤，否则已取消订单会看不到原座位。

索引：`ix_booking_seats_booking(booking_id)`。

---

## 9. `tickets` 电子票

| 列 | 类型 | 可空 | 默认 | 约束/说明 |
|---|---|---|---|---|
| `id` | INTEGER | 否 | 自增 | 主键 |
| `booking_id` | INTEGER | 否 | — | FK → `bookings.id`，且 `UNIQUE`（一预约一票） |
| `ticket_code` | TEXT | 否 | — | 20 位 Crockford Base32，`UNIQUE` |
| `verified_at` | TEXT | 是 | `NULL` | 首次核验时间；未核验为 NULL |
| `verified_by` | INTEGER | 是 | `NULL` | FK → `users.id`；核验主办方 |

> `tickets` 表**没有** `status` 列。票面状态由 `bookings.status` 与 `verified_at` 派生，规则见 `docs/contracts/enums.md §2.5`。

---

## 10. 枚举汇总

| 枚举 | 值 |
|---|---|
| `Role` | `user` / `organizer` |
| `EventStatus` | `draft` / `published` / `closed` / `cancelled` |
| `EventSeatStatus` | `available` / `locked` / `sold` |
| `BookingStatus` | `reserved` / `cancelled` / `used` |
| `TicketStatus`（派生） | `reserved` / `cancelled` / `used` |
| `SeatType` | `standard` |

---

## 11. 索引与约束速查

| 名称 | 表 | 定义 | 作用 |
|---|---|---|---|
| `ux_booking_seats_active` | `booking_seats` | `(event_id, seat_id) WHERE is_active=1` 唯一 | 防重复占座；取消后可重订 |
| `ix_bookings_user` | `bookings` | `(user_id, created_at DESC, id DESC)` | 我的预约分页 |
| `ix_event_seats_event` | `event_seats` | `(event_id, status)` | 按活动查状态/统计 |
| `ix_booking_seats_booking` | `booking_seats` | `(booking_id)` | 查一次预约的座位 |
| `tickets.ticket_code` | `tickets` | 唯一 | 票号全局唯一 |
| `tickets.booking_id` | `tickets` | 唯一 | 一预约一票 |
| `event_seats(event_id, seat_id)` | `event_seats` | 唯一 | 一场活动一个座位一行 |
| `seats(venue_id,row_number,seat_number)` | `seats` | 唯一 | 同场馆同排同座唯一 |

---

## 12. 连接级设置（`repos/database.py`）

| 设置 | 值 | 作用 |
|---|---|---|
| `journal_mode` | `WAL` | 读不阻塞写 |
| `foreign_keys` | `ON` | 真正执行外键 |
| `busy_timeout` | `15000ms` | 抢不到写锁时排队等待 |
| `row_factory` | `sqlite3.Row` | 行映射按列名读取 |
| 事务 | `BEGIN IMMEDIATE` | 事务开始即申请写锁 |
