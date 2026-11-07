# SeatVerse · 接口契约（API）

> 状态：已冻结 ｜ 负责人：A ｜ 日期：2026-11-06
> 覆盖：通路前缀、统一响应信封、17 个接口的路径与归属、关键接口响应形态与样例
> 依据：02 号《后端开发规范》§三 / §八、04 号《开发路线图》§3.1—3.7、05 号《六人分工方案》接口分工

---

## 1. `/api` 前缀口径

### 1.1 一句话结论

**对外 URL 与后端最终源码路由统一为 `/api/...`。`/api` 只在后端的 `APIRouter(prefix="/api")` 声明一次；装饰器内 path 不重复写 `/api`。不使用 `--root-path`，开发代理与生产网关都原样转发、不剥前缀。**

### 1.2 路径对照

| 层 | 形态 | 登录接口示例 | 负责人 |
|---|---|---|---|
| 对外契约（文档 / 浏览器 / curl） | **含** `/api` 前缀 | `/api/authentication/login` | 全体 |
| 前端代码（`endpoints.ts` 的 path） | **不含**前缀，以 `/` 开头 | `/authentication/login` | A |
| 前端 `baseURL` / `VITE_API_BASE` | `/api`，无尾斜杠 | — | A |
| 后端挂载（`APIRouter(prefix="/api")` + `@router.post(...)`） | 装饰器 path **不含**前缀，最终挂载路径**含** | `@router.post("/authentication/login")` → `/api/authentication/login` | D |
| 后端实际收到（经 Vite 代理原样转发） | **含**前缀 | `/api/authentication/login` | 代理 |

拼接公式只有一条：**`请求 URL = baseURL + path = "/api" + "/authentication/login"`**；后端最终路由 = `/api` + 装饰器 path，与请求 URL 一致。

### 1.3 五条约定

#### 后端：`/api` 由 router 统一声明

- 所有业务 router 必须挂到 `APIRouter(prefix="/api")` 下；装饰器 path 不得再以 `/api` 开头，否则会出现 `/api/api/...`。
- 模块 router 通过 `router.include_router(module_router)` 挂在同一前缀下；不要在模块装饰器或子 router 上重复写 `/api`。
- 理由：前缀属于 API 命名空间，写在 router 上可集中管理，也避免每个接口重复字符串。

#### 启动：不再使用 `--root-path`

- `uv run poe dev` / `uv run poe start` 直接启动 `uvicorn main:app`，不带 `--root-path`。
- `--root-path` 只适用于“网关剥掉 `/api`”的方案；本契约的网关不剥前缀，因此不使用。
- 禁止把 `--root-path` 与 `APIRouter(prefix="/api")` 同时使用：那会让路由匹配先剥一层前缀，导致 404，并让 OpenAPI 出现 `/api/api/...`。

#### 前端：`baseURL` 与 `path` 各司其职

- `const baseURL = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/+$/, "")`：末尾斜杠归一，空值回落 `/api`。
- `endpoints.ts` 的每个路径必须以 `/` 开头、不含 `/api`、不含双斜杠。
- 页面与组件禁止拼 `/api`；也不得出现 `/api/api/...` 这类重复前缀。
- `request("/")` 是健康检查入口，拼接结果为 `/api/`。

#### 开发代理：原样转发，不 rewrite

`frontend/vite.config.ts` 的 `server.proxy` 必须保持下面这份配置：

```ts
server: {
  proxy: {
    "^/api/": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
  },
},
```

- **删除 `rewrite`**：后端路由本身带 `/api`，代理剥前缀会让后端收到 `/authentication/login`，与源码路由 `/api/authentication/login` 不匹配。
- 匹配键是 `^/api/`，要求前缀后必须带 `/`。因此所有请求路径都要以 `/` 开头（见上文「前端」），不要直接请求裸 `/api`。
- `vite preview` 默认没有代理。配置 `preview` 时把**同一份** proxy 复制过去（同样不带 `rewrite`），保证 `npm run dev` 与 `npm run preview` 都能通过 `http://localhost:<port>/api/` 访问后端。

#### 生产部署：同源 + 原样转发

- 静态前端与 API 部署在**同源**下，浏览器只发 `/api/...`，不跨域直连 `:8000`。
- 反向代理（Nginx / 学校网关）把 `/api/*` 原样转发到后端 `/api/*`，**不剥掉 `/api`**。
- 生产不依赖 CORS。后端的 CORS 白名单只服务本机直连调试，见 `backend/.env.example`。

### 1.4 与 02 号文档 §八"统一 `/api` 前缀"的关系

02 号 §八写"路由分组：按模块分组，统一 `/api` 前缀"。本节与该条一致：源码路由的最终挂载路径统一含 `/api`，由 `APIRouter(prefix="/api")` 落地，不做"对外前缀 / 源码前缀"的二分解释。

### 1.5 变更点与回退

| 若有人主张 | 改动量 | 结论 |
|---|---|---|
| 改用 `--root-path=/api` 且源码路由不带前缀 | 去掉 router prefix + 恢复 Vite `rewrite` + 改全部文档 | 不采用（前缀归属摇摆、网关必须剥前缀） |
| 前端 `baseURL` 改成 `http://localhost:8000` | 改 `.env` + 放弃同源代理 + 处理 CORS | 不采用（把开发问题带进部署） |
| 生产网关剥前缀 | 后端需改用 root-path 或反向改写 | 不采用（与本节"网关不剥"冲突） |

### 1.6 验证

```bash
cd SeatVerse

# 1) 后端 router 统一声明 /api 前缀（预期 1 条）
grep -n 'APIRouter(prefix="/api")' backend/main.py

# 2) 启动参数不再带 root-path（预期无输出）
grep -n 'root-path' backend/pyproject.toml

# 3) 前端代理不再 rewrite（预期无输出）
grep -n 'rewrite' frontend/vite.config.ts

# 4) 前端路径常量不含 /api（预期无输出）
grep -rn '"/api' frontend/src/common/api

# 5) 开发链路：终端 1 / 终端 2 分别常驻启动
(cd backend && uv run poe dev)       # 终端 1
(cd frontend && npm run dev)         # 终端 2

# 6) 终端 3 验证
curl -s http://localhost:8000/api/   # {"code":200,"message":"ok","payload":"Hello from SeatVerse!"}
curl -s http://localhost:5173/api/   # 同上，证明代理原样转发生效
```

反证（可选，验证后改回）：临时删掉 `backend/main.py` 的 `prefix="/api"`，`curl http://localhost:8000/api/` 应变成 404——证明前缀确由源码路由声明。

---

## 2. 统一响应信封（基线，引用 02 号 §三）

所有接口 **HTTP 状态码恒为 200**，业务结果只看响应体顶层 `code`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | `number` | `200` 成功；其余为错误码 |
| `message` | `string` | 可直接展示的中文提示 |
| `payload` | 泛型 / `null` | 业务数据；失败时通常为 `null` |

| code | 含义 | 前端动作 |
|---|---|---|
| 200 | 成功 | 返回 `payload`（可能为 `null`，由调用方判空） |
| 400 | 参数或业务规则不允许 | 显示 `message` |
| 401 | 未登录 / 令牌过期 / 账号密码错误 | 按 `auth.md` §7，登录与注册页只显示不跳转 |
| 403 | 权限不足 | 显示 `message`，不跳登录 |
| 404 | 资源不存在 | 显示 `message`；票号场景统一"不存在或无权查看" |
| 409 | 状态冲突 | 显示后端 `message`；选座提交的 409 刷新座位状态并提示重选（02 §三、03 §六）；重复签到 409 按 03 §8 展示首次签到时间 |

**前端兜底**：后端目前尚未接管 `HTTPException` 与 `RequestValidationError`，非 2xx 响应体是 `{"detail": ...}`。请求客户端必须先尝试按信封解析；解析失败一律抛 `ApiError(-1, MALFORMED_RESPONSE_MESSAGE)`，**不得读取 HTTP 状态码、不得按 404/422/5xx 分支**，页面展示固定中文文案、不得白屏（02 §三、03 §六、04 §3.1）。

**分页**：列表统一 `{ items, total, page, pageSize }`，`page` 从 1 开始，`pageSize` 默认 20、上限 100；单对象接口直接返回对象，不包分页。`total` 是满足条件的总条数，不是当前页条数。具体排序与查询参数见 §4.1。

---

## 3. 接口索引（17 个）

表中"路由内 path"是后端 `@router` 里应写的值（**不含** `/api`）；最终挂载路径 = `/api` + 本列，由 `APIRouter(prefix="/api")` 统一加前缀。对外路径与最终挂载路径相同，不得出现第三种写法。

| # | 方法 | 对外路径 | 路由内 path | 权限 | 负责人 | 备注 |
|---|---|---|---|---|---|---|
| 1 | POST | `/api/authentication/register` | `/authentication/register` | 公开 | D | 注册即登录，响应见 `auth.md` §14 |
| 2 | POST | `/api/authentication/login` | `/authentication/login` | 公开 | D | 响应见 `auth.md` §14 |
| 3 | GET | `/api/authentication/me` | `/authentication/me` | 登录 | D | `payload` 为 user 对象本身 |
| 4 | GET | `/api/events` | `/events` | 公开 | D | 支持关键词 / 状态筛选与分页 |
| 5 | GET | `/api/events/{id}` | `/events/{id}` | 公开 | D | — |
| 6 | POST | `/api/events` | `/events` | 主办方 | D | 创建后默认草稿 |
| 7 | PATCH | `/api/events/{id}/status` | `/events/{id}/status` | 归属主办方 | D | 发布 / 关闭预约 / 取消 |
| 8 | GET | `/api/venues` | `/venues` | 公开 | E | 第一版恒返回 1 条 |
| 9 | GET | `/api/venues/{id}/seats` | `/venues/{id}/seats` | 公开 | E | 静态坐标 |
| 10 | GET | `/api/events/{id}/seats` | `/events/{id}/seats` | 公开 | E | 该场动态座位状态 |
| 11 | POST | `/api/bookings` | `/bookings` | 登录 | E | 座位冲突返回 409 |
| 12 | POST | `/api/bookings/{id}/cancel` | `/bookings/{id}/cancel` | 归属本人 | E | 取消后座位恢复可预约；返回形态见 §4.2 |
| 13 | GET | `/api/bookings/me` | `/bookings/me` | 登录 | E | 分页，票号内联；见 §4.1 |
| 14 | GET | `/api/bookings/{id}/ticket` | `/bookings/{id}/ticket` | 归属本人 | F | 含票号、座位、活动；非本人/不存在统一 404 |
| 15 | GET | `/api/tickets/{ticket_code}` | `/tickets/{ticket_code}` | 登录 | F | 票号直查；非本人/不存在统一 404 |
| 16 | GET | `/api/events/{id}/bookings` | `/events/{id}/bookings` | 归属主办方 | F | 本场预约名单 |
| 17 | POST | `/api/tickets/verify` | `/tickets/verify` | 主办方 | F | 请求体 `{ticketCode}`，返回 Ticket；重复核验 409 |

约定：

- 路径参数一律在客户端 `encodeURIComponent` 后拼接。
- 资源名用复数、动作接口用动词子路径，不带版本号（04 号 §3.2）。
- 新增接口在 `/api` router 下按路由内 path 写（不含 `/api`），再在此表登记。

---

## 4. 关键接口数据形态

本节冻结“我的预约、取消、电子票”三组接口的字段与样例。字段名统一 **camelCase**；时间统一 ISO 8601 带时区偏移（样例为 `+08:00`）。

### 4.1 `GET /api/bookings/me`

**查询参数**

| 参数 | 类型 | 必填 | 默认 | 约束 |
|---|---|---|---|---|
| `page` | integer | 否 | `1` | `>= 1`，越界返回 `400` |
| `pageSize` | integer | 否 | `20` | `1—100`，越界返回 `400` |

- 只返回当前登录用户的预约，包含 `reserved` / `cancelled` / `used` 三种状态。
- `Booking.status` 只返回这三个存储值；“已完成 / 已签到”是展示态，按 `enums.md` §2.7 由前端从时间与状态派生，不写入接口。
- **不做服务端状态分组**，也不接受 `status` 查询参数。04 §3.6 的“按状态分组”是页面展示要求：接口按 02 §三返回分页列表，前端用 `$derived` 本地分组；服务端重复分组会与 02 的分页契约冲突。
- 排序固定为 `createdAt DESC, id DESC`，保证同一时间创建的多条记录顺序稳定。
- 返回 `Page<Booking>`：`{ items, total, page, pageSize }`。

**`Booking` 字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | integer | 是 | 预约编号，正整数 |
| `status` | `"reserved" \| "cancelled" \| "used"` | 是 | 见 `enums.md` |
| `createdAt` | string | 是 | 创建时间，ISO 8601 |
| `cancelledAt` | string \| null | 是 | 未取消为 `null`；`cancelled` 时非空 |
| `ticketCode` | string | 是 | 内联票号，20 位；规则见 `ticket-qr.md` |
| `event` | `EventSummary` | 是 | 活动摘要 |
| `seats` | `SeatBrief[]` | 是 | 至少 1 个；按 `row`、`number` 升序 |

**`EventSummary` 字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | integer | 是 | 活动编号 |
| `title` | string | 是 | 活动标题 |
| `status` | `"draft" \| "published" \| "closed" \| "cancelled"` | 是 | 见 `enums.md` |
| `startTime` | string | 是 | 开始时间，ISO 8601 |
| `endTime` | string | 是 | 结束时间，ISO 8601，必须晚于 `startTime` |
| `venue` | `{ id: integer, name: string }` | 是 | 场馆编号与名称 |

**`SeatBrief` 字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | integer | 是 | 座位编号，与选座页 `seat_id` 对齐 |
| `row` | integer | 是 | 排号，`>= 1` |
| `number` | integer | 是 | 座号，`>= 1` |
| `label` | string | 是 | 展示名，固定格式 `{row}排{number}号` |
| `seatType` | `"standard"` | 是 | 第一版只有普通座 |

**样例**：`samples/bookings-me.ok.json`

### 4.2 `POST /api/bookings/{id}/cancel`

**请求**

- 路径参数 `id`：预约编号，正整数；非整数返回 `400`。
- 无请求体；客户端携带请求体时后端忽略。
- 权限：登录 + 预约本人。

活动是否已停止预约**不影响取消**：只要预约属于本人、状态为 `reserved`、活动尚未开始，用户都可以取消。

**成功响应 `payload`**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer | 被取消的预约编号 |
| `status` | `"cancelled"` | 固定为 `cancelled` |
| `cancelledAt` | string | 取消时间，ISO 8601 |

`message` 使用后端成功文案；样例中为 `"ok"`。

**错误语义**

| code | 触发条件 | 前端动作 |
|---|---|---|
| `400` | 活动已开始或已结束；参数非法 | 显示 `message` |
| `401` | 未登录 / 令牌失效 | 由请求客户端统一清令牌并跳登录 |
| `403` | 预约不属于当前用户 | 显示 `message`，不跳登录 |
| `404` | 预约不存在 | 显示 `message` |
| `409` | 预约已是 `cancelled` 或 `used`（重复取消、已签到） | 显示后端 `message`；前端不特化、不自动重拉（除选座提交与 03 §8 的重复签到外，其余 409 一律只展示 `message`） |

**副作用（同一事务）**

1. `bookings.status = "cancelled"`，写入 `cancelledAt`。
2. `tickets` 不新增状态列；票面 `status` 按派生规则变为 `cancelled`（见 `enums.md` §2.5）。
3. `booking_seats` 有效标记置为无效，关联 `event_seats.status` 回到 `available`。
4. 取消成功后前端派发跨页事件，规则见 `frontend-arch.md` §7。

**样例**：`samples/booking-cancel.ok.json`；重复取消样例：`samples/error.409.json`。

### 4.3 电子票读取与核验

`GET /api/bookings/{id}/ticket` 与 `GET /api/tickets/{ticket_code}` **返回同一形状的 `Ticket`**。

**`Ticket` 字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | integer | 是 | 电子票编号 |
| `bookingId` | integer | 是 | 对应预约编号 |
| `ticketCode` | string | 是 | 20 位票号，规则见 `ticket-qr.md` |
| `status` | `"reserved" \| "cancelled" \| "used"` | 是 | 派生字段：预约已取消 → `cancelled`；已核验 → `used`；否则 `reserved` |
| `issuedAt` | string | 是 | 出票时间，ISO 8601；等于对应预约的 `createdAt`（同一事务生成，不单独存储） |
| `verifiedAt` | string \| null | 是 | 未核验为 `null`；`used` 时非空 |
| `verifiedBy` | integer \| null | 是 | 核验人用户编号；未核验为 `null` |
| `event` | `EventSummary` | 是 | 同 §4.1 |
| `seats` | `SeatBrief[]` | 是 | 同 §4.1 |

**权限与不存在的处理**

| 接口 | 权限 | 非本人 / 不存在 |
|---|---|---|
| `GET /api/bookings/{id}/ticket` | 登录 + 预约本人 | 统一 `404`，不区分“预约不存在”与“不是本人” |
| `GET /api/tickets/{ticket_code}` | 登录 | 统一 `404`，不区分“票号不存在”与“他人票” |

- 票号先按 `ticket-qr.md` §2.3 归一化再查询。
- 未登录返回 `401`，由请求客户端统一处理。
- `POST /api/tickets/verify` 请求体 `{ "ticketCode": "..." }`；成功返回更新后的完整 `Ticket`（`status = "used"`）；权限、重复核验与活动状态规则见 `ticket-qr.md` §4.2。

**二维码内容**：04 §3.6 要求电子票“含二维码内容”。本契约不单独返回 `qrContent` 字段：`Ticket.ticketCode` 的规范形式即二维码内容（`ticket-qr.md` §3.1），前端直接用 `ticketCode` 渲染二维码，避免同一规则维护两处。

**样例**：`samples/ticket.ok.json`。

### 4.4 样例索引

| 文件 | 对应接口 | 说明 |
|---|---|---|
| `samples/login.ok.json` | `POST /api/authentication/login` | 登录成功，`payload = { token, user }` |
| `samples/bookings-me.ok.json` | `GET /api/bookings/me` | 分页 + 两条不同状态的预约 |
| `samples/booking-cancel.ok.json` | `POST /api/bookings/{id}/cancel` | 取消成功 |
| `samples/ticket.ok.json` | `GET /api/bookings/{id}/ticket` | 与列表样例中 `id = 9001` 的预约对应 |
| `samples/error.409.json` | 重复取消冲突 | 失败信封，`payload = null` |

样例规则：

1. 每个文件必须是完整信封，字段齐全，JSON 可解析。
2. 失败样例的 `payload` 必须为 `null`。
3. 样例值只用于字段对照，不导入数据库，不代表真实令牌或真实票号。
4. 修改字段时同一提交内同步改样例、本节、`enums.md` / `ticket-qr.md` 与前端 `types.ts`。

---

## 5. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-05 | 定稿：通路前缀口径、统一响应信封、17 个接口索引 | A |
| 2026-11-06 | 冻结：预约分页与字段、取消返回形态、电子票字段、样例索引 | A |
| 2026-11-06 | 对齐 01—05：兜底文案不读 HTTP 状态、取消 409 不特化、分组与二维码内容口径澄清 | A |
