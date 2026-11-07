# 登录令牌存储契约

> 状态：已定稿 ｜ 负责人：A ｜ 日期：2026-11-05
> 适用：路由守卫、登录态 store、统一请求客户端
> 依据：02 号《后端开发规范》§三、03 号《前端开发规范》§五/§六、04 号《开发路线图》§3.3
> 实现位置：`frontend/src/common/stores/auth.svelte.ts`（登录态 store 建立时创建）；本文件是唯一口径来源

---

## 1. 一句话结论

**令牌存 `localStorage` 的 `seatverse.auth.token`；用户信息存 `seatverse.auth.user`，仅作缓存；token 是唯一权威，启动时有 token 必须回源 `GET /authentication/me`，网络失败不清 token，只有 401 才清。**

**401 例外**：`/authentication/login`、`/authentication/register` 的 401 不清令牌、不跳转，只渲染表单文案；其余接口 401 清令牌并跳 `#/login?next=<当前路径>`，并发只跳一次。

**传输（见 §14）**：请求头 `Authorization: Bearer <token>`；登录成功 `payload = { token, user: { id, name, email, role } }`；过期一律表现为 HTTP 200 + body `code = 401`，不使用 HTTP 401。

---

## 2. 存储介质与作用域

| 项 | 结论 | 理由 |
|---|---|---|
| 介质 | `localStorage` | 静态托管、无后端会话 cookie；刷新与 hash 路由切换后仍保持登录 |
| 作用域 | 同源共享。开发态 `http://localhost:5173`；生产为静态托管同源 | 不是跨域单点登录，换源即换会话，属预期行为 |
| 不使用 | `sessionStorage`、cookie、IndexedDB | 前两者关标签即失效或引入后端 cookie 语义；IndexedDB 对两个短字符串属过度设计 |
| 明文风险 | 令牌以明文存放 | XSS 一旦成立即等价于令牌泄露；缓解措施见 §10 |

---

## 3. 键名与值格式（约定）

```ts
// 唯一定义处：frontend/src/common/stores/auth.svelte.ts
export const TOKEN_STORAGE_KEY = "seatverse.auth.token";
export const USER_STORAGE_KEY = "seatverse.auth.user";
```

| 键 | 常量 | 类型 | 值格式 | 读写方 |
|---|---|---|---|---|
| `seatverse.auth.token` | `TOKEN_STORAGE_KEY` | `string` | 服务端令牌**原文**：不含 `Bearer ` 前缀、不加引号、写入前 `trim()` | 仅 auth store |
| `seatverse.auth.user` | `USER_STORAGE_KEY` | JSON 字符串 | `JSON.stringify(User)`，`User` 即 `GET /authentication/me` 的 `payload` | 仅 auth store |

**值的判定规则**

1. token 缺失、空串、纯空白 → 一律视为**未登录**，不得发起 `me` 请求。
2. token 值恰为字符串 `"null"` / `"undefined"` → 视为脏数据，归一为未登录并删除该键（防手改 localStorage 后误判）。
3. `seatverse.auth.user` 只是**服务端用户对象的序列化镜像**：字段名由 §14.2 固定为 `id / name / email / role`，同步到 `src/common/api/types.ts`。D 后续**新增**字段不需要改本契约（前端忽略未知字段）；**删除或改名**属破坏性变更，必须同时改 §14.2、`samples/login.ok.json` 与 `types.ts`。
4. **禁止**在 `auth.svelte.ts` 以外的任何文件硬编码这两个字符串字面量；页面与请求层只能消费 store 暴露的 API。
5. **禁止**把令牌写入 URL、query、标题、日志或错误文案（见 §10）。

---

## 4. 权威性与启动回源

| 规则 | 内容 |
|---|---|
| 唯一权威 | token。user 缓存可缺失、可过期、可被用户手改，**任何角色判断都不得只依赖缓存** |
| 令牌形态 | 前端**不解析 JWT**，不假设令牌结构、不做本地过期计时；过期一律由后端以 `code === 401` 表达 |
| 角色用途 | 仅用于界面显隐与路由分流；权限**以后端为准**（03 §五：二次校验在服务端） |
| 启动回源 | 存在有效 token 时，`bootstrap()` 必须请求 `GET /authentication/me`，用返回值覆盖 user 缓存；缓存只用于首屏占位，不作为身份结论 |

---

## 5. 启动流程与状态机

```
idle ──bootstrap()──► loading ──me 成功──────────► authed
                        │
                        ├── me 返回 401 ──────────► guest（并 clear）
                        └── 网络失败/超时 ────────► guest（保留 token，不跳转）
无 token ──bootstrap()───────────────────────────► guest（不发请求）
```

| 场景 | 行为 |
|---|---|
| `status === "idle"` | 尚未判定登录态，守卫必须先 `await auth.bootstrap()` 再决定跳转 |
| 无 token | 直接 `guest`，**不**请求 `me` |
| 有 token 且 `me` 成功（`code === 200`） | 覆盖 `user` 缓存，`status = "authed"` |
| 有 token 且 `me` 返回 401 | `clear()`（两键均删），`status = "guest"` |
| 有 token 但网络失败 / 超时 / 非统一信封 | **保留 token**，`status = "guest"`，**不跳转**——用于区分“没登录”与“网断了” |
| `bootstrap()` 被并发调用 | 可重入：共享同一个 in-flight Promise，`me` 只发一次 |

**执行时机**：`App.svelte` 的 `onMount` 中先 `auth.bootstrap()`，再 `router.init()`，保证首次路由守卫执行时登录态已就绪（应用壳落地时接入）。

---

## 6. 写入与清除时机

| 触发点 | 动作 |
|---|---|
| 登录成功（`POST /authentication/login` 返回 200） | `setSession(token, user?)`：**先写 token、后写 user**；用户信息可空，由 `bootstrap()` 回源补齐 |
| 主动登出 | `clear()` → `navigate("/login", { replace: true })`；**先清后跳**，避免守卫读到旧 token |
| `bootstrap()` 收到 401 | `clear()` |
| 请求层收到非白名单 401 | `clear()`；跳转与并发去重按 §7 执行 |
| 跨标签页 token 消失 | `clear()`（见 §8） |

**`clear()` 的语义（硬性）**

1. 使用 `removeItem` 删除两个键，**禁止**写 `null`、`"null"`、`""` 等占位值。
2. **幂等**：重复调用不抛错、不产生副作用。
3. 删除顺序：**先删 user、后删 token**，让观察者以 token 消失作为“已登出”的判定点。
4. 仅清本地，不发任何网络请求。

**写入权限**：只有 auth store 能写这两个键。请求客户端、页面组件、路由守卫一律只读 store 状态。

---

## 7. 401 处理与跳转例外

> 背景：后端 HTTP 恒 200，登录失效只体现在响应体 `code === 401`（02 §三、03 §六）。

### 7.1 白名单：不清令牌、不跳转

| 路径（不含 `/api` 前缀） | 401 时的行为 |
|---|---|
| `/authentication/login` | 视为“账号或密码错误”：只在登录表单内渲染 `message`；**保留**本地已有令牌，不改登录态 |
| `/authentication/register` | 视为注册失败：同上，只渲染 `message` |

- 白名单按**完整路径精确匹配**（`endpoints` 中的路径不含前缀），不做前缀或模糊匹配，防止误放行其它接口。
- 判定只发生在统一请求客户端，页面不重复判断。

### 7.2 其余接口的 401

1. `auth.clear()`：删除两个存储键（见 §6）。
2. 跳转 `#/login?next=<encodeURIComponent(当前完整 hash 路径)>`，使用 `replace`，避免历史堆栈堆积。
3. **并发去重**：模块级 `let redirecting = false`；同一次“过期风暴”只跳一次，跳转完成后用 `setTimeout(() => { redirecting = false; }, 0)` 复位。
4. 仍然向调用方抛 `ApiError(401, message)`；页面只负责展示文案，**不得再跳一次**，避免二次跳转覆盖 `next`。

### 7.3 `next` 的生成、校验与回跳

| 环节 | 规则 |
|---|---|
| 生成 | 只取 hash 中的路径与查询串（如 `/bookings`、`/bookings?tab=used`），**绝不包含 origin** |
| 校验 | 登录页读取时必须先 `decodeURIComponent` 再做本地路径校验：以 `/` 开头、不以 `//` 开头、不含 `\`、不含 `:`（协议 / 盘符），不满足一律回退 `/`（防开放重定向） |
| 回跳 | 登录成功后 `navigate(next, { replace: true })`，随后清除 `next` 查询参数 |
| 一致性 | 路由守卫与请求层产生的 `next` 使用同一套生成规则 |

### 7.4 与 `bootstrap()` 的关系

- `bootstrap()` 的 `me` 返回 401：只 `clear()`，**不跳转**，避免刷新首屏就把用户弹走；下一次进入受保护路由时由守卫跳转。
- 网络失败不是 401：不清令牌、不跳转（§5）。

---

## 8. 跨标签页同步

监听 `window.addEventListener("storage", ...)`：

| 事件后重读 token 的结果 | 动作 |
|---|---|
| token 变为 `null`（含 `localStorage.clear()` 触发、`event.key === null` 的情况） | 本标签页 `clear()`，并以 `replace` 方式跳 `/login` |
| token 变为**新的非空值**（另一标签页登录/换账号） | 更新本标签页 token，`status = "loading"`，回源 `me` |
| token 未变（只是 user 缓存变化） | 忽略，身份以回源结果为准 |

约束：

1. **不信任 `event.key`**：`localStorage.clear()` 时 `event.key === null`，因此一律重读 `TOKEN_STORAGE_KEY` 判断，而不是按 key 名分支。
2. 多标签页并发登录不同账号采用 **last-write-wins**：后写者覆盖，先写者被同步登出；本契约不阻止，也不提供“合并会话”。
3. `storage` 事件**不会**在写入的同一个标签页触发，本标签页的更新必须走 store 方法，不能依赖该事件。

---

## 9. 失败模式与降级

| 故障 | 处理 |
|---|---|
| `localStorage` 不可用（隐私模式、被禁用、`SecurityError`） | 降级为**内存态**：token 仅本标签页有效；`console.warn` 一次；**不阻塞渲染、不弹模态框** |
| 写入抛 `QuotaExceededError` | 同内存态降级；不得让登录流程失败 |
| `seatverse.auth.user` 非法 JSON（手改缓存） | `try/catch` 捕获，删除该键，视为无缓存；身份仍以回源结果为准，**不得让应用白屏** |
| token 为空白字符 / `"null"` / `"undefined"` | 归一为未登录并清除（§3） |
| 登出后、`me` 响应才迟到 | 请求层只返回结果，**不得写会话**；store 在 `clear()` 后忽略迟到的 `me` 结果，防止会话复活 |
| `bootstrap()` 被并发调用 | 共享 in-flight Promise（§5） |

所有 try/catch 只做降级，**不得吞掉错误后假装成功**：无法判定时状态置 `guest`，由页面三态（加载/空/错误）正常展示。

---

## 10. 安全约束

1. 禁止 `console.log` 打印 token，禁止把 token 拼进错误文案、URL、`document.title` 或任何可能经 referrer 外泄的位置。
2. 令牌有效期、签名与撤销由后端（D）负责；本契约不引入前端加密（`localStorage` 内的加密无法防 XSS，只会制造“已加密”的错觉）。
3. 退出登录使用 `replace` 跳转，防止浏览器后退回到受保护页；受保护页进入时仍需重新校验 `status`。
4. 前端守卫只是体验层（03 §五），后端必须独立校验身份、角色与资源归属。
5. 页面渲染外部数据时禁止 `{@html}` 直出未转义内容，以降低 XSS 导致令牌泄露的概率。

---

## 11. 边界与归属

| 事项 | 归属 | 最晚 | 本契约的接口点 |
|---|---|---|---|
| 请求头名称、是否带 `Bearer ` 前缀、登录响应 `payload` 字段名 | 已定稿（见 §14） | — | `Authorization: Bearer <token>`、`payload = { token, user }`；改口径只动 `AUTH_HEADER` / `AUTH_SCHEME` 两个常量，令牌存储格式不变 |
| 票号不属于当前用户时返回 403 还是 404 | 已定稿：**404**（防枚举，见 `ticket-qr.md` §4） | — | 与本契约无关；401 处理仍按本文档 |
| 本契约的实现（store、状态机、降级） | A | S2 | 实现必须逐条满足 §3—§10 |
| 统一请求客户端（注入令牌、401 分支） | A | S2 | 只读 store，不直接读写 `localStorage` |

---

## 12. 命名口径说明

04 号《开发路线图》§0.3 规定“鉴权命名一律 `authentication` 全名、禁止 `auth` 缩写”，该条约束的是 **HTTP 路径段与后端模块名**（如 `/authentication/login`、后端 `authentication.py`；§3.2“鉴权模块用 `authentication`”同此范围）。

本文件与 storage 键名沿用既有写法 `seatverse.auth.*` 与文件名 `auth.md`，不视为冲突：

- URL 中一律 `authentication`，不得出现 `/auth/...`；
- 本地存储前缀 `seatverse.auth.` 与前端目录/文件名 `auth.svelte.ts`、`auth.md` 保持不变。

若组内要求严格统一，只需修改 `TOKEN_STORAGE_KEY` / `USER_STORAGE_KEY` 两个常量；旧键可直接弃用（用户需重新登录一次），**无数据迁移成本**。

---

## 13. 验收自检清单（登录态 store 落地时逐条执行）

| # | 操作 | 预期 |
|---|---|---|
| 1 | DevTools 执行 `localStorage.setItem("seatverse.auth.token", "fake-token")` 后刷新 | Network 出现一次 `GET /api/authentication/me`；未登录时不发 |
| 2 | 用坏令牌刷新 | `me` 返回 401 后两键均被删除，状态为 `guest` |
| 3 | 停掉后端后带 token 刷新 | token **仍在**，状态 `guest`，页面无未捕获异常、不跳登录 |
| 4 | 手改 `seatverse.auth.user` 为 `{` | 应用正常启动，该键被清除，身份以回源为准 |
| 5 | 打开两个标签页，在 A 页登出 | B 页自动清除并跳登录（`replace`） |
| 6 | 在 A 页登录，B 页处于打开状态 | B 页 token 更新并重新回源 `me` |
| 7 | 关闭浏览器后重开 | 仍保持登录（localStorage 持久化生效） |
| 8 | 在登录页提交错误密码（后端返回 401） | **停留在登录页**，表单显示后端 `message`，令牌未被清除 |
| 9 | 已登录后把令牌改成垃圾值，再请求受保护接口 | 两个存储键被清除并跳 `#/login?next=...`；连续多个请求只跳一次 |

---

## 14. 令牌传输契约

> 本节是 `client.ts` 与 `auth.login()` 的唯一实现依据。
> 冲突说明：早期草案写的是 `{ token, user: { id, username, role } }`。`users` 表字段是“编号 / 姓名 / 邮箱 / 密码散列 / 角色”，没有 `username`，故**以本节为准**：`id / name / email / role`。

### 14.1 结论表

| 项 | 结论 | 说明 |
|---|---|---|
| 请求头名称 | `Authorization` | HTTP 头名大小写不敏感；代码统一写这个拼写 |
| 认证方案 | `Bearer` | 按 RFC 6750；`Bearer` 与令牌之间是**一个半角空格** |
| 头值格式 | `Bearer ${token}` | 令牌用服务端返回的**原文**，不含 `Bearer `、不加引号 |
| 无令牌时 | **不发送**该请求头 | 不写 `Bearer `、不写空值、不占位 |
| 登录 / 注册请求 | **强制不发送**该请求头 | 防止本地旧令牌干扰"账号或密码错误"的判定 |
| 其它传递方式 | **禁止** | 不得用 query、cookie、请求体传令牌 |
| 过期表现 | **HTTP 200 + body `code = 401`** | 不使用 HTTP 401；不要求 `WWW-Authenticate`；前端按 §7 处理 |
| 令牌结构 | 对前端**不透明** | 不解析 JWT、不读 `exp`、不做本地过期计时 |
| 有效期与续期 | 由后端决定 | 第一版无 refresh token；过期即重新登录 |
| 传输安全 | 开发态同源代理；生产同源或 HTTPS | 令牌只走请求头，见 §10 |

### 14.2 登录响应 `payload` 字段表

```json
{
  "token": "sv_2b7f4c9e1a6d8f3c5e0b9a7d2c4f6e81",
  "user": { "id": 2, "name": "演示用户", "email": "user@seatverse.local", "role": "user" }
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `token` | `string` | 是 | 非空；不含 `Bearer ` 前缀；原样写入 `seatverse.auth.token` |
| `user` | `object` | 是 | 与 `GET /authentication/me` 的 `payload` **同结构、同字段名、同类型** |
| `user.id` | `integer` | 是 | 正整数；仅用于展示与本地关联，**权限以后端为准** |
| `user.name` | `string` | 是 | 非空；界面显示名（对应 `users.姓名`） |
| `user.email` | `string` | 是 | 注册邮箱，登录账号 |
| `user.role` | `"user" \| "organizer"` | 是 | 只有两个值，定义见 `enums.md`；中文标签由前端映射 |

**五条硬约束**

1. 登录成功的 `payload` 顶层只有 `token` 与 `user`，**不再嵌套** `payload.data` 之类的中间层。
2. 不要求返回 `expiresIn`、`refreshToken`、`tokenType`；若后端返回，前端忽略，不得据此改变会话逻辑。
3. `user` **新增**字段向后兼容，前端忽略未知字段；**删除或改名**属破坏性变更，必须同一次提交内改本节、样例与 `types.ts`。
4. `login` 的 `user` 与 `me` 的 `payload` 必须同构：**`me` 的 `payload` 就是 user 对象本身**，不再包一层 `{ "user": ... }`；否则首屏缓存与回源结果会打架（§4）。
5. 注册接口与登录同构（注册即登录）：成功返回同样的 `{ token, user }`，前端注册成功后直接进入登录态。

### 14.3 前端落地常量与注入顺序

```ts
// 唯一定义处：frontend/src/common/api/client.ts
export const AUTH_HEADER = "Authorization";
export const AUTH_SCHEME = "Bearer ";
const AUTH_EXEMPT_PATHS = [
  "/authentication/login",
  "/authentication/register",
] as const;
```

注入判定顺序（**不可调换**）：

1. 路径命中 `AUTH_EXEMPT_PATHS` → 不注入；
2. `auth.token` 为空（`null` / 空串 / 纯空白）→ 不注入；
3. 其余 → `headers[AUTH_HEADER] = AUTH_SCHEME + token`。

约束：

- 注入只发生在 `client.ts` 一处；页面、store、其它模块**禁止**自行设置 `Authorization`。
- 令牌不得出现在 URL、日志、错误文案、`document.title` 或任何可被 referrer 外泄的位置（§10）。
- 若后续改用其它头名（如 `X-Auth-Token`）或去掉 `Bearer `，只改 `AUTH_HEADER` / `AUTH_SCHEME` 两行；存储键、白名单、401 逻辑均不变。
- `/api` 前缀与拼接规则见 `docs/contracts/api.md` §1，与本节相互独立。

### 14.4 失效与错误的判定口径

| 场景 | 后端返回 | 前端动作 |
|---|---|---|
| 未带令牌 | HTTP 200，`code = 401`，`message` 中文，`payload = null` | 按 §7.2 清令牌并跳登录（登录页/注册页除外） |
| 头格式错 / 令牌非法 / 已过期 | 同上；`message` 为"登录已失效，请重新登录" | 按 §7.2 |
| 登录邮箱或密码错 | 同上 `code = 401`；`message` 为"邮箱或密码错误" | 按 §7.1 白名单，只显示、不清不跳 |
| 令牌有效但角色不足 | `code = 403` | 显示 `message`，**不跳登录** |
| 后端未接管的 404/422 | HTTP 404/422 + `{"detail": ...}` | 先按信封解析；失败一律 `ApiError(-1, MALFORMED_RESPONSE_MESSAGE)`，**不读状态码、不按 404/422 分支**，展示固定中文、不白屏（02 §三、03 §六） |

### 14.5 样例与验证

- 样例文件：`docs/contracts/samples/login.ok.json`（字段与 §14.2 逐字对应，样例令牌非真实值）。
- 登录接口交付后，按下表逐条自测。

| # | 操作 | 预期 |
|---|---|---|
| 1 | `POST /api/authentication/login` 正确账号密码 | `code = 200`；`payload.token` 非空；`payload.user.role` ∈ `user` / `organizer` |
| 2 | 带 `Authorization: Bearer <token>` 请求 `GET /api/authentication/me` | `code = 200`；返回的 `user` 与登录时逐字段一致 |
| 3 | 不带该头请求 `me` | `code = 401`，`payload = null`，HTTP 仍是 200 |
| 4 | 带 `Authorization: Bearer garbage` 请求 `me` | `code = 401`（不是 403、不是 500） |
| 5 | 浏览器 Network 看登录请求 | 请求头**没有** `Authorization`（即使本地残留旧令牌） |
| 6 | 浏览器 Network 看登录后的 `me` 请求 | 请求头为 `Authorization: Bearer <token>`，无多余空格、无引号 |

---

## 15. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-05 | 首版确定：令牌存储与启动回源、401 白名单例外与跳转去重 | A |
| 2026-11-05 | 补充令牌传输契约：`Authorization: Bearer`、登录 `payload = { token, user }`、失效表现（§14） | A |
| 2026-11-06 | 复核：令牌头、登录 `payload` 与 `samples/login.ok.json` 一致，无字段变更 | A |
| 2026-11-06 | 对齐 02/03：非信封响应统一格式异常文案，不按 HTTP 状态码分支 | A |
