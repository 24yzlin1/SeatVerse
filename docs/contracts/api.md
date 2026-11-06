# SeatVerse · 接口契约（API）

> 状态：已定稿 ｜ 负责人：A ｜ 日期：2026-11-05
> 覆盖：通路前缀、统一响应信封、17 个接口的路径与归属
> 依据：02 号《后端开发规范》§三 / §八、04 号《开发路线图》§3.1—3.7、05 号《六人分工方案》接口分工

---

## 1. `/api` 前缀口径

### 1.1 一句话结论

**对外 URL 一律 `/api/...`；后端源码路由一律不写 `/api`。`/api` 只允许出现在三个地方：后端启动参数 `--root-path=/api`、前端 `baseURL` / `VITE_API_BASE`、开发与生产的反向代理规则。**

### 1.2 三层路径对照

| 层 | 形态 | 登录接口示例 | 负责人 |
|---|---|---|---|
| 对外契约（文档 / 浏览器 / curl） | **含** `/api` 前缀 | `/api/authentication/login` | 全体 |
| 前端代码（`endpoints.ts` 的 path） | **不含**前缀，以 `/` 开头 | `/authentication/login` | A |
| 前端 `baseURL` / `VITE_API_BASE` | `/api`，无尾斜杠 | — | A |
| 后端源码路由（`@router.post(...)`） | **不含**前缀 | `@router.post("/authentication/login")` | D |
| 开发态后端实际收到（经 Vite 代理剥前缀） | 不含前缀 | `/authentication/login` | 代理 |

拼接公式只有一条：**`请求 URL = baseURL + path = "/api" + "/authentication/login"`**。

### 1.3 五条约定

#### 后端：路由不写 `/api`

- `APIRouter` 不得设置 `prefix="/api"`；`@router.get` / `@router.post` 的 path 不得以 `/api` 开头。
- 后端 Python 代码里不得出现字符串字面量 `/api`；它只出现在 `pyproject.toml` 的启动参数、`.env.example`、README 与文档中。
- 理由：前缀描述的是**部署位置**，不是资源标识。写进路由会导致换部署路径时改全部路由，且与 `--root-path` 叠加成 `/api/api/...`。

#### 启动：`--root-path=/api` 由 `poe` 统一带上

- `uv run poe dev` / `uv run poe start` 已带 `--root-path=/api`，这是唯一推荐的启动方式。
- `--root-path` 的职责是让 OpenAPI 文档、生成的 URL 与重定向把对外前缀声明为 `/api`；它**不是**路由前缀，代码里看不到 `/api`。
- 禁止用 `uvicorn main:app`（不带 `--root-path`）做联调或演示：文档前缀、部署转发都会与契约不一致。

#### 前端：`baseURL` 与 `path` 各司其职

- `const baseURL = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/+$/, "")`：末尾斜杠归一，空值回落 `/api`。
- `endpoints.ts` 的每个路径必须以 `/` 开头、不含 `/api`、不含双斜杠。
- 页面与组件禁止拼 `/api`；也不得出现 `/api/api/...` 这类重复前缀。
- `request("/")` 是健康检查入口，拼接结果为 `/api/`。

#### 开发代理：保留 rewrite 剥前缀

`frontend/vite.config.ts` 的 `server.proxy` 必须保持下面这份配置：

```ts
server: {
  proxy: {
    "^/api/": {
      target: "http://localhost:8000",
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ""),
    },
  },
},
```

- **保留 `rewrite`**：不要因为"后端有 `--root-path=/api`"就删掉。两者职责不同——rewrite 决定转发到后端的实际路径，`--root-path` 只影响文档与 URL 生成。
- 匹配键是 `^/api/`，要求前缀后必须带 `/`。因此所有请求路径都要以 `/` 开头（见上文「前端」），不要直接请求裸 `/api`。
- `vite preview` 默认没有代理。配置 `preview` 时把**同一份** proxy 复制过去，保证 `npm run dev` 与 `npm run preview` 都能通过 `http://localhost:<port>/api/` 访问后端。

#### 生产部署：同源 + 剥前缀转发

- 静态前端与 API 部署在**同源**下，浏览器只发 `/api/...`，不跨域直连 `:8000`。
- 反向代理（Nginx / 学校网关）把 `/api/*` 转发到后端 `/*`，**剥掉 `/api`**，与开发态一致。
- 生产不依赖 CORS。后端的 CORS 白名单只服务本机直连调试，见 `backend/.env.example`。

### 1.4 与 02 号文档 §八"统一 `/api` 前缀"的口径澄清

02 号 §八写"路由分组：按模块分组，统一 `/api` 前缀"。本契约将其解释为**对外 URL 统一 `/api` 前缀**，而不是源码路由前缀；实现方式固定为 `--root-path=/api` + 反向代理剥前缀。

若组内坚持在源码路由里写 `/api`，必须同时删掉 `vite.config.ts` 的 `rewrite`（一行改动），且 OpenAPI 文档路径会变成 `/api/api/...`。**不采用。** 口径只允许一种，自本节定稿起不再讨论。

### 1.5 变更点与回退

| 若有人主张 | 改动量 | 结论 |
|---|---|---|
| 后端路由带 `/api` | 删 `rewrite` 一行 + 改全部路由 + 改 OpenAPI | 不采用（重复前缀、迁移成本高） |
| 前端 `baseURL` 改成 `http://localhost:8000` | 改 `.env` + 放弃同源代理 + 处理 CORS | 不采用（把开发问题带进部署） |
| 生产网关不剥前缀 | 后端需额外接受 `/api` 前缀（依赖框架 root-path 行为） | 不采用（把框架实现细节当契约） |

### 1.6 验证

```bash
cd SeatVerse

# 1) 后端源码不含 /api 路由（预期无输出）
grep -rn '"/api' backend/app backend/main.py

# 2) 启动参数带 root-path（预期 dev / start 各一条）
grep -n 'root-path' backend/pyproject.toml

# 3) 前端路径常量不含 /api（预期无输出）
grep -rn '"/api' frontend/src/common/api

# 4) 开发链路：终端 1 / 终端 2 分别常驻启动
(cd backend && uv run poe dev)       # 终端 1
(cd frontend && npm run dev)         # 终端 2

# 5) 终端 3 验证
curl -s http://localhost:8000/       # {"code":200,"message":"ok","payload":"Hello from SeatVerse!"}
curl -s http://localhost:5173/api/   # 同上，证明代理与 rewrite 生效
```

反证（可选，验证后改回）：临时删掉 `rewrite` 那一行，`curl http://localhost:5173/api/` 应变成 404——证明剥前缀确由 rewrite 完成。

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
| 409 | 状态冲突 | 显示特化文案并触发刷新 |

**前端兜底**：后端目前尚未接管 `HTTPException` 与 `RequestValidationError`，非 2xx 响应体是 `{"detail": ...}`。请求客户端必须先尝试按信封解析，失败则按 `ApiError(-1, "服务异常（HTTP xxx）")` 抛出，页面不得白屏（按请求客户端的兜底分支实现）。

**分页**：列表统一 `{ items, total, page, pageSize }`，`page` 从 1 开始；单对象接口直接返回对象，不包分页。

---

## 3. 接口索引（17 个）

表中"源码路由"是后端 `@router` 里应写的值，"对外路径"是浏览器与文档里出现的值。两者只差 `/api`，不得出现第三种写法。

| # | 方法 | 对外路径 | 源码路由 | 权限 | 负责人 | 备注 |
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
| 12 | POST | `/api/bookings/{id}/cancel` | `/bookings/{id}/cancel` | 归属本人 | E | 取消后座位恢复可预约 |
| 13 | GET | `/api/bookings/me` | `/bookings/me` | 登录 | E | 当前用户的预约列表 |
| 14 | GET | `/api/bookings/{id}/ticket` | `/bookings/{id}/ticket` | 归属本人 | F | 含票号、座位、活动 |
| 15 | GET | `/api/tickets/{ticket_code}` | `/tickets/{ticket_code}` | 登录 | F | 票号直查 |
| 16 | GET | `/api/events/{id}/bookings` | `/events/{id}/bookings` | 归属主办方 | F | 本场预约名单 |
| 17 | POST | `/api/tickets/verify` | `/tickets/verify` | 主办方 | F | 重复核验返回 409 |

约定：

- 路径参数一律在客户端 `encodeURIComponent` 后拼接。
- 资源名用复数、动作接口用动词子路径，不带版本号（04 号 §3.2）。
- 新增接口先按"源码路由无前缀"写，再在此表登记。

---

## 4. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-05 | 定稿：通路前缀口径、统一响应信封、17 个接口索引 | A |
