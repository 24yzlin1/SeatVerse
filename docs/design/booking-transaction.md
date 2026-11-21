# 预约 / 取消 / 核验事务时序

> 负责人：E（预约与取消）｜ 合作：F（票务核验）｜ 日期：2026-11-21
> 对应代码：`app/core/bookings.py`、`app/core/tickets.py`、`app/repos/bookings.py`、`app/repos/seats.py`、`app/repos/tickets.py`

---

## 1. 预约创建 `POST /api/bookings`

```mermaid
sequenceDiagram
    autonumber
    participant C as 选座页
    participant S as scope/bookings
    participant K as core/bookings
    participant R as repos
    participant DB as SQLite

    C->>S: POST /api/bookings {eventId, seatIds}
    S->>S: 校验登录、eventId、非空、seatIds 不重复
    S->>K: create_booking(identity, request)
    K->>DB: BEGIN IMMEDIATE
    K->>R: find_event_for_booking_in_transaction(event_id)
    R->>DB: SELECT events
    alt 活动不存在
        K-->>C: 404 活动不存在
    else 草稿/停止预约/已取消/已开始/已结束
        K-->>C: 400 对应文案
    end

    loop 每个 seat_id
        K->>R: mark_event_seat_sold(event_id, seat_id)
        R->>DB: UPDATE event_seats<br/>SET status='sold', version=version+1<br/>WHERE status='available'
        alt rowcount = 1
            Note over K: 该座抢占成功
        else rowcount = 0
            K-->>C: 409 座位刚刚被预约，请重新选择
            Note over DB: ROLLBACK，前面已占的座恢复
        end
    end

    K->>R: insert_booking(...)
    R->>DB: INSERT bookings (status='reserved')

    loop 每个 seat_id
        K->>R: insert_booking_seat(...)
        R->>DB: INSERT booking_seats (is_active=1)
    end

    K->>K: 生成 20 位 Crockford Base32 票号
    K->>R: insert_ticket(connection, booking_id, ticket_code)
    R->>DB: INSERT tickets
    Note over K,R: 票号唯一冲突时重试，最多 5 次

    K->>DB: COMMIT
    K->>R: find_booking_detail + list_booking_seats
    K-->>S: BookingPublic
    S-->>C: {code:200, payload: Booking}
```

关键点：

- `BEGIN IMMEDIATE` 在第一步就拿写锁，避免两个请求同时读到“空闲”；
- 座位判断写在 `UPDATE ... WHERE status='available'` 里，看 `rowcount`，不先 SELECT 再 UPDATE；
- 预约、座位关联、票在同一事务，任一步失败整体 `ROLLBACK`；
- 多座预约不会出现“A 座成功、B 座失败但 A 已写入”。

---

## 2. 取消 `POST /api/bookings/{id}/cancel`

```mermaid
sequenceDiagram
    autonumber
    participant A as 我的预约页
    participant S as scope/bookings
    participant K as core/bookings
    participant R as repos
    participant DB as SQLite

    A->>S: POST /api/bookings/{id}/cancel
    S->>S: 校验登录、id 为正整数
    S->>K: cancel_booking(identity, booking_id)
    K->>DB: BEGIN IMMEDIATE
    K->>R: find_booking_in_transaction(booking_id)
    R->>DB: SELECT bookings

    alt 预约不存在
        K-->>A: 404
    else 不是本人
        K-->>A: 403
    else status 不是 reserved
        K-->>A: 409 已取消/已签到
    else 活动已开始/已结束
        K-->>A: 400
    end

    K->>R: mark_booking_cancelled(booking_id, cancelled_at)
    R->>DB: UPDATE bookings SET status='cancelled'<br/>WHERE status='reserved'<br/>AND NOT EXISTS (verified ticket)
    alt rowcount != 1
        K-->>A: 409 状态已变化
    end

    K->>R: active_booking_seat_ids(booking_id)
    R->>DB: SELECT seat_id WHERE is_active=1

    loop 每个有效座位
        K->>R: release_event_seat(event_id, seat_id)
        R->>DB: UPDATE event_seats SET status='available'<br/>WHERE status='sold'
        alt rowcount != 1
            K-->>A: 409 座位状态已变化
            Note over DB: ROLLBACK
        end
    end

    K->>R: deactivate_booking_seats(booking_id)
    R->>DB: UPDATE booking_seats SET is_active=0
    K->>DB: COMMIT
    K-->>S: CancelBookingPayload
    S-->>A: {id,status:"cancelled",cancelledAt}
```

关键点：

- 活动 `closed` **不影响取消**；只要求本人、`reserved`、活动尚未开始；
- `booking_seats` 置 `is_active=0`，但历史行保留；“我的预约”仍显示原座位；
- 票不单独改状态，票面状态按 `bookings.status` 派生为 `cancelled`；
- 取消与核验都在写事务里重查状态，避免“已取消仍签到”。

---

## 3. 核验 `POST /api/tickets/verify`（F 负责）

```mermaid
sequenceDiagram
    autonumber
    participant O as 主办方核验页
    participant S as scope/tickets
    participant K as core/tickets
    participant R as repos/tickets
    participant DB as SQLite

    O->>S: POST /api/tickets/verify {ticketCode}
    S->>S: 要求 organizer 角色；角色不足 403
    S->>K: verify_ticket(identity, ticketCode)
    K->>K: 归一化票号 + 格式校验；非法 404
    K->>DB: BEGIN IMMEDIATE
    K->>R: find_ticket_by_code(connection, ticketCode)
    R->>DB: SELECT tickets + bookings + events
    alt 票不存在或不属于本主办方活动
        K-->>O: 404（统一文案，防枚举）
    else 已核验
        K-->>O: 409 + 首次核验时间
    else 预约已取消 / 已 used
        K-->>O: 409
    else 活动已取消 / 已结束
        K-->>O: 409
    end

    K->>R: mark_ticket_verified(ticket_id, verified_at, verified_by)
    R->>DB: UPDATE tickets SET verified_at=?, verified_by=?<br/>WHERE verified_at IS NULL
    K->>R: mark_booking_used(booking_id)
    R->>DB: UPDATE bookings SET status='used'<br/>WHERE status='reserved'
    K->>DB: COMMIT
    K-->>O: TicketPublic(status="used")
```

关键点：

- 核验与取消使用同一套写事务纪律：`BEGIN IMMEDIATE` + 条件更新；
- 重复核验返回 409，并回显首次核验时间；
- 票号不属于本主办方活动时返回 404，不区分“不存在/他人票”。

---

## 4. 取消 vs 核验的竞争

两个事务都会先拿写锁，因此只会有一方先提交：

| 先提交的操作 | 后提交的操作看到的数据库状态 | 后提交结果 |
|---|---|---|
| 核验成功 | `bookings.status='used'`、`tickets.verified_at` 非空 | 取消返回 409，座位保持 `sold` |
| 取消成功 | `bookings.status='cancelled'`、`event_seats.status='available'` | 核验返回 409，座位保持 `available` |

代码层面的双保险：

- 取消的 `UPDATE bookings` 带 `status='reserved' AND NOT EXISTS (verified ticket)`；
- 核验先查 `verified_at IS NULL`、`booking_status != cancelled`，再条件更新 `tickets` 与 `bookings`。

自动化证据：`backend/tests/test_booking_ticket_race.py`，覆盖：

1. 先核验 → 再取消，409；
2. 先取消 → 再核验，409；
3. 两线程同时取消/核验，恰好一方 200、一方 409，数据库状态与胜者一致。

---

## 5. 错误码速查

| 场景 | code |
|---|---|
| 未登录 / token 失效 | 401 |
| 参数非法、活动不可预约、活动已开始/结束、取消已开始的活动 | 400 |
| 预约/座位/票不存在，票不属于当前用户或本主办方活动 | 404 |
| 不是预约本人、不是 organizer | 403 |
| 座位被抢、重复取消、重复核验、已取消仍核验、活动取消/结束仍核验 | 409 |

所有接口 HTTP 恒为 200，业务结果看响应体顶层 `code`。

---

## 6. 与测试的对应

| 事务点 | 测试 |
|---|---|
| 预约成功/重复提交/多座回滚 | `tests/test_booking_flow.py` |
| 10 用户同座并发 | `tests/test_concurrency.py` + `scripts/concurrency_test.py` |
| 取消后重订、我的预约 | `tests/test_booking_flow.py` |
| 取消/核验竞争 | `tests/test_booking_ticket_race.py` |
| 外键与有效占用唯一 | `tests/test_constraints.py` |
