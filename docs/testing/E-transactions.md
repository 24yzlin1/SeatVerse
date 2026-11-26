# E · 预约事务与并发验收记录

> 日期：2026-11-21 ｜ 负责人：E ｜ 状态：P0 / P1 已完成
> 适用：`docs/requirements/05_SeatVerse_六人分工方案.md` 中 E 的 7 条用例、并发验收与取消/核验竞争要求

---

## 1. 结论

- E 的 7 条事务/并发用例已落成 pytest，**11 条测试全部通过**（含 1 条重复座位编号校验、3 条取消/核验竞争用例）。
- 10 个独立用户经真实 HTTP 抢同一座位，实测 **1 个业务 200、9 个业务 409**，数据库只有 1 份有效占用和 1 张票。
- 测试使用独立临时库 / 隔离库，**没有修改 `backend/.db/data.db` 演示库**。
- `uv run poe check`（含 tests）零错误。

---

## 2. 自动化测试

执行：

```powershell
cd backend
uv run pytest -q
```

结果：

```text
...........                                                              [100%]
11 passed, 1 warning in 25.55s
```

| # | 测试 | 覆盖的 E 用例 |
|---|---|---|
| 1 | `tests/test_database_init.py::test_empty_database_initialization` | 空库初始化：8 表、11 用户、120 座位、4 活动、360 活动座位 |
| 2 | `tests/test_booking_flow.py::test_event_seat_isolation` | 活动座位隔离：event 2 的 1 号座 sold，event 3 的 1 号座仍 available |
| 3 | `tests/test_booking_flow.py::test_duplicate_submission` | 重复提交：1×200、1×409，仅 1 张票 |
| 4 | `tests/test_concurrency.py::test_ten_users_race_for_same_seat` | 10 用户同座并发：1×200、9×409，1 份有效占用、1 张票 |
| 5 | `tests/test_booking_flow.py::test_multi_seat_rollback` | 多座回滚：`[空闲2, 已售1]` 失败后座位 2 仍 available，无残留预约 |
| 6 | `tests/test_booking_flow.py::test_cancel_and_rebook` | 取消后重订：取消后座位恢复、列表仍显示原座位、同座可再次预约 |
| 7 | `tests/test_constraints.py::test_foreign_key_and_active_unique_index` | 外键有效性 + `booking_seats` 有效占用部分唯一索引 |
| 8 | `tests/test_constraints.py::test_duplicate_seat_ids_rejected` | 请求内重复 `seatIds` 返回 400 |
| 9 | `tests/test_booking_ticket_race.py::test_cancel_after_verify_returns_409` | 先核验后取消：取消 409，预约 used，座位 sold |
| 10 | `tests/test_booking_ticket_race.py::test_verify_after_cancel_returns_409` | 先取消后核验：核验 409，预约 cancelled，座位 available |
| 11 | `tests/test_booking_ticket_race.py::test_concurrent_cancel_and_verify_only_one_wins` | 两线程同时取消/核验：恰好一方 200、一方 409，数据库状态一致 |

测试隔离方式：

- `tests/conftest.py` 的 `database_path` fixture 为每个用例创建 `tmp_path/seatverse-test.db`；
- 通过 `SEATVERSE_DATABASE_PATH` 指向临时库，再调用 `scripts.seed.seed_all(reset=True)`；
- `client` fixture 用 `TestClient(main.app)` 触发应用生命周期，但数据库仍是临时库；
- 用例结束临时目录由 pytest 清理。

> `tests/test_concurrency.py` 直接并发调用 `create_booking`，验证事务与 SQLite 锁；真实 HTTP 并发由下一节的官方脚本验证。

---

## 3. 真实 HTTP 并发验收

### 3.1 准备隔离库与账号（只在本地，不提交）

先停掉正在运行的后端，避免复制到未落盘的 WAL 数据：

```powershell
cd backend

# 1) 生成一份干净的演示库
uv run python -m scripts.seed --reset

# 2) 复制到本地忽略目录（.local-checks/ 已在 .gitignore 中）
New-Item -ItemType Directory -Force ..\.local-checks | Out-Null
Copy-Item .db\data.db ..\.local-checks\c07-live.db

# 3) 生成 10 个开发账号 JSON（与 seed 的 user01—user10 一致）
$accounts = 1..10 | ForEach-Object {
    [pscustomobject]@{
        email    = ('user{0:D2}@seatverse.local' -f $_)
        password = 'User12345!'
    }
}
$json = ConvertTo-Json -InputObject @($accounts) -Compress
[IO.File]::WriteAllText(
    (Join-Path (Resolve-Path ..\.local-checks).Path 'c07-accounts.json'),
    $json,
    [Text.UTF8Encoding]::new($false)
)
```

检查目标座位初始为空闲：

```powershell
cd backend
$env:SEATVERSE_DATABASE_PATH = (Resolve-Path ..\.local-checks\c07-live.db).Path
uv run python -c "import sqlite3, os; c=sqlite3.connect(os.environ['SEATVERSE_DATABASE_PATH']); print(c.execute('select status from event_seats where event_id=2 and seat_id=1').fetchone()[0])"
```

应输出 `available`。

### 3.2 启动隔离服务

```powershell
cd backend
$env:SEATVERSE_DATABASE_PATH = (Resolve-Path ..\.local-checks\c07-live.db).Path
$env:SEATVERSE_JWT_SECRET = 'c07-local-secret-0123456789abcdef'
uv run uvicorn main:app --port 8000
```

> `main.py` 的 `load_dotenv()` 不会覆盖已存在的进程环境变量，因此这里会使用隔离库，而不是 `.env` 里的演示库。

### 3.3 执行并发脚本

另开一个终端：

```powershell
cd backend
uv run python -m scripts.concurrency_test `
  --base-url http://127.0.0.1:8000/api `
  --event-id 2 `
  --seat-id 1 `
  --accounts ..\.local-checks\c07-accounts.json `
  --database ..\.local-checks\c07-live.db `
  --cleanup
```

实测输出：

```json
{"http200":10,"success":1,"conflicts":9,"activeOccupancy":1,"tickets":1,"noOrphans":true,"winnerMatched":true,"cleanedUp":true}
```

脚本断言：

| 断言 | 结果 |
|---|---|
| 10 个请求 HTTP 全部 200 | ✅ |
| 业务码：1 个 200、9 个 409 | ✅ |
| `event_seats` 目标座为 `sold` | ✅ |
| `booking_seats` 有效占用恰好 1 条 | ✅ |
| 目标座对应票据恰好 1 张 | ✅ |
| 成功请求的预约 id/用户与数据库占用一致 | ✅ |
| 失败请求没有留下孤儿预约或票 | ✅ |
| `--cleanup` 取消成功后座位恢复 `available` | ✅ |

### 3.4 收尾

```powershell
# 停掉隔离服务后
Remove-Item -Recurse -Force ..\.local-checks
```

`backend/.db/data.db` 演示库不受影响；本次核对的演示库状态为：

```text
bookings: 0
tickets: 0
event 2 seat 1: available
```

---

## 4. 与 `05` 号分工的对应关系

| `05` 要求 | 当前证据 |
|---|---|
| 空库初始化 | `test_empty_database_initialization` + `scripts.migrate` / `scripts.seed` |
| 活动座位隔离 | `test_event_seat_isolation` |
| 重复提交 | `test_duplicate_submission` |
| 同座并发 1 成 9 败 | `tests/test_concurrency.py` + `scripts/concurrency_test.py` |
| 多座回滚 | `test_multi_seat_rollback` |
| 取消后重订 | `test_cancel_and_rebook` |
| 外键与有效占用唯一性 | `test_foreign_key_and_active_unique_index` |
| 取消 / 核验竞争 | `tests/test_booking_ticket_race.py` 三条用例 |
| 并发结果留存 | 本文档第 3 节 |

---

## 5. 仍未覆盖（可选增强）

- `GET /bookings/me` 的 `eventId/status` 组合筛选可再补接口级用例。
- 前端选座页收到 409 后刷新动态座位的交互，属于 C 的前端测试，不在本后端测试范围。
