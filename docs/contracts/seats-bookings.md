# 座位与预约接口交接（E → C）

状态：2026-11-21 按当前后端实现核对；本文件固定可供 `frontend-alt` 使用的契约，不代表已经取得队友的人工签字。

统一请求前缀为 `/api`。下列接口始终返回 HTTP 200，业务结果读取顶层 `{ code, message, payload }`；成功为 `code=200`。前端复用 `@/common/api` 的请求与登录态，不能自行保存或注入令牌。

## 座位数据

`GET /api/venues/{id}/seats` 返回 `{ items: [...] }`，每个座位有 `id`、`row`、`number`、`label`、`seatType`、`x`、`y`、`z`。

- `id`、场馆与活动编号、`row`、`number` 均为正整数，不能转换成字符串编号，也不能用数组下标生成编号。
- `row` 和 `number` 从 1 开始；`label` 为“1排1号”这类展示名；`seatType` 当前仅为 `standard`。
- 坐标为有限数值，单位米；X 向右、Y 向上、Z 从舞台指向后排。前端原样使用 `[x,y,z]`。目前固定场馆 10 排 × 12 座，共 120 座；座位来自后端种子数据，不能在前端重新计算业务布局。
- 座位 ID 全局唯一；坐标和排座组合不可重复。活动详情的 `venue.capacity` 应与完整静态座位数量一致。空列表表示尚未配置座位，禁止预约。

`GET /api/events/{id}/seats` 返回 `{ items: [{ seatId, status }] }`。`seatId` 关联上一个接口的 `id`，与 `event_seats.id` 无关。同一物理座位在不同活动中的状态独立。

- `available`：可选；`sold`：已被有效预约占用；`locked`：预留枚举，第一版不写入，前端按不可选处理。
- 已发布及关闭预约的活动应返回该场馆全部座位的状态，不能将缺失或未知状态默认为空闲。草稿尚未初始化动态座位，禁止预约。
- 场馆或活动不存在为业务码 404；路径参数非法为 400。

样例：[静态座位](samples/venue-seats.ok.json)、[不存在的场馆](samples/venue-not-found.error.json)、[活动动态座位](samples/event-seats.ok.json)、[不存在的活动](samples/seatmap-not-found.error.json)。静态和动态样例均包含完整 120 座。

## 提交预约

`POST /api/bookings` 需要有效登录态，公共客户端发送 `Authorization: Bearer <token>`。请求体严格为 `{ eventId: number, seatIds: number[] }`，座位集合非空、编号唯一，所有编号为正整数；布尔值、浮点编号、额外字段均不接受。

成功 `payload` 为完整 `Booking`，包括真实 `id`、`status=reserved`、`createdAt`、`cancelledAt=null`、20 位 Crockford Base32 `ticketCode`、活动摘要 `event` 和本次全部 `seats`。返回座位集合必须与请求完全一致，每个编号只能出现一次。前端可以原地展示预约编号和票号，并提供“我的预约／电子票”入口。

- `400`：请求无效，活动尚未发布、已关闭、取消、开始或结束。
- `401`：未登录或令牌无效。公共客户端统一清除登录态，选座模块提示重新登录，不重复管理身份。
- `404`：活动或座位不存在；座位不属于活动场馆。
- `409`：座位刚刚被占用，包括重复提交同一座位。前端重新获取动态状态，移除失效选择，保留仍有效选择。
- 网络中断、非法成功体或 5xx：提交结果可能已经入库；不自动重试 POST，提示先到“我的预约”核对。

预约事务使用 `BEGIN IMMEDIATE`，逐座条件更新，并在同一事务写入预约、座位关联和票据。多座任一失败整体回滚，不产生部分占用、预约或票据。前端选择仅为本地意向，不代表锁座。

样例：[请求](samples/booking-create.request.json)、[成功](samples/booking-create.ok.json)、[抢座冲突](samples/booking-conflict.error.json)、[非法请求](samples/booking-invalid.error.json)、[未登录](samples/booking-unauthorized.error.json)。成功样例是独立验证库中的示例预约，不能当作已有业务记录使用。

## 新版前端所需的查询补充

`GET /api/bookings/me` 新增可组合的可选查询参数：`eventId` 为正整数，`status` 为 `reserved`、`used`、`cancelled`，多个状态以逗号分隔。筛选在分页之前执行，`total` 仅计算筛选后的本人预约；不传参数保持原行为。空状态、未知状态或非法活动编号返回业务码 400。仍按创建时间与编号倒序，`pageSize` 上限 100；前端应提供分页或继续加载，不能只读前 100 条后自行过滤。

`GET /api/events/{id}/seat-statistics` 公开返回 `{ eventId, total, sold, locked, available, updatedAt }`，外层仍是标准成功信封。统计在数据库中按本场已初始化的动态座位聚合，`total = sold + locked + available`；未发布且未初始化座位的活动各项为 0，不虚构可预约座位。`updatedAt` 为带时区的查询时间。活动不存在为 404，非法编号为 400。详情页使用此接口展示参与统计，选座仍使用明确列出的三个真实查询与客户端校验。

## 开始条件与验证

C-07 开始前须验证：新版客户端可编译，真实登录和 `/authentication/me` 可用；上述座位数据能完整关联；有效活动能创建真实预约；失败信封符合约定。文档样例不替代实际运行验证。

E 的十用户并发命令为 `backend/scripts/concurrency_test.py`，对已经启动的真实 API 发送十个同时释放的线程请求。调用者明确提供独立验证库、活动、空闲座位及十个开发账号，命令断言 1 个业务 200、9 个业务 409、HTTP 全部 200、数据库仅一份有效占用及对应票据。`--cleanup` 在验证后取消成功预约并检查座位释放。不要对正在使用的业务活动运行并发验收。

在 `backend/` 执行：

```powershell
uv run python -m scripts.concurrency_test --base-url http://127.0.0.1:8000/api --event-id 2 --seat-id 1 --accounts ..\.local-checks\c07-accounts.json --database ..\.local-checks\c07-live.db --cleanup
```

账号文件是十项 `{ "email": "开发账号", "password": "开发密码" }` 的 JSON 数组，保存在本地忽略目录；命令不打印密码或令牌。并发后的数据库断言和多座回滚用例共同构成后端证据，浏览器演示不替代事务验证。
