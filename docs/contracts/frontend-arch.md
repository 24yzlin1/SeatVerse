# 前端路由与目录契约

> 状态：已冻结 ｜ 负责人：A ｜ 日期：2026-11-08
> 适用：路由、应用壳，以及 B / C / F 的全部页面
> 依据：03 号《前端开发规范》§一 / §五
> 说明：本文确定“路由怎么组织、代码放哪里”，以及取消预约后的跨页一致性；不涉及具体页面实现

---

## 1. 结论：hash 路由

### 1.1 形态

| 项 | 结论 |
|---|---|
| 路由形态 | hash：`http://localhost:5173/#/bookings` |
| 实现 | 自研极简路由（约 60—90 行），**零第三方依赖** |
| 不使用 | `history` API 路由、SvelteKit、`svelte-spa-router` 等路由库 |
| 与后端关系 | 前端路由完全独立，后端不需要任何 rewrite 回退 |

### 1.2 理由

1. 静态托管（GitHub Pages 或任意静态服务器）刷新不会 404，不需要服务器配置 fallback。
2. hash 变化不触发页面请求，`hashchange` 事件天然对应路由更新，浏览器后退 / 前进免费可用。
3. 本项目不做 SSR / SEO，URL 带 `#` 的代价可接受。
4. 零依赖 = 无版本冲突、不改锁文件。

### 1.3 代价与边界

- URL 带 `#`，不美观；但分享链接完整可用。
- hash 部分不会发送到服务器，后端日志看不到前端路由（本项目不需要）。
- 部署无需额外配置；`vite preview` 与静态托管行为一致。

### 1.4 明确不做

- 不做无 `#` 的美化路由（需要服务器 rewrite，与静态托管冲突）。
- 不做嵌套路由与路由级代码分割（页面数量少，收益低）。

---

## 2. URL 契约

### 2.1 组成

| 组成 | 示例 | 说明 |
|---|---|---|
| hash 路径 | `#/events/9/seats` | 唯一路由依据 |
| 查询串 | `#/login?next=%2Fbookings` | 用 `URLSearchParams` 解析 |
| 动态段 | `/events/:id` | 参数 `id = "9"` |
| 默认入口 | `#`、`#/`、`/` | 归一为 `/`，再重定向到 `/events` |

### 2.2 归一规则

1. 空 hash、`#`、`#/` 一律当作 `/`。
2. 去掉结尾多余斜杠（`/events/` → `/events`），根路径除外。
3. 动态段在匹配前逐个 `decodeURIComponent`（中文、空格必须能还原）。
4. 查询串不参与路径匹配，原样保留。

### 2.3 禁止

- 禁止把令牌、密码、个人信息放进 hash 或 query（见 `auth.md` §10）。
- 禁止用 `#` 以外的形式承载前端路由。
- 页面不得自己读写 `location.hash`，只能调用 `navigate()`。

---

## 3. 匹配、守卫与历史

### 3.1 匹配优先级

1. 静态段优先于动态段；同层级按段数从多到少。
2. 全部不匹配 → `*` 兜底 → 404 页。
3. 动态参数缺段（如 `#/events//seats`）视为不匹配。

### 3.2 守卫顺序

`redirect` → `requiresAuth` → `roles`：

| 情况 | 行为 |
|---|---|
| 命中 `redirect` | 改写到目标路径（`/` → `/events`），使用 `replace` |
| 未登录访问受保护路由 | 跳 `#/login?next=<encodeURIComponent(hash 的路径与查询串，不含 #)>`，`replace` |
| 已登录但角色不符 | 回各自首页：普通用户 `/events`，主办方 `/organizer/events` |
| 登录成功后的落点 | 有 `next` 回 `next`；否则普通用户 `/events`，主办方 `/organizer/events` |
| `status === "idle"` | 先 `await auth.bootstrap()` 再判断（见 `auth.md` §5） |

登录页成功回调必须走该落点；`next` 的校验规则见 `auth.md` §7.3。

守卫只做体验层拦截；角色与资源归属的最终判定**以后端为准**（03 §五）。

### 3.3 历史与生命周期

1. `init()` 时先手动解析一次（首次进入没有 `hashchange` 事件）。
2. 同时监听 `hashchange` 与 `popstate`；`destroy()` 移除全部监听。
3. `navigate()` 用 `location.hash = "#" + to`；`replace` 时用 `history.replaceState` 后**手动触发一次解析**（`replaceState` 不触发事件）。
4. 同一路径重复 `navigate` 直接 return，避免重复请求。
5. 浏览器后退 / 前进必须能回到上一条路由（验收项）。

### 3.4 路由清单（实现时照此建立）

| # | 路径 | 页面 | 守卫 |
|---|---|---|---|
| 1 | `/` | 重定向到 `/events` | — |
| 2 | `/login` | `LoginPage` | 公开 |
| 3 | `/register` | `RegisterPage` | 公开 |
| 4 | `/events` | `EventsPage` | 公开 |
| 5 | `/events/:id` | `EventDetailPage` | 公开 |
| 6 | `/events/:id/seats` | `SeatMapPage` | 公开 |
| 7 | `/bookings` | `BookingsPage` | 需登录 |
| 8 | `/bookings/:id/ticket` | `TicketPage` | 需登录 |
| 9 | `/tickets/:code` | `TicketByCodePage` | 需登录 |
| 10 | `/organizer/events` | `OrganizerEventsPage` | 需登录 + organizer |
| 11 | `/organizer/events/:id/bookings` | `OrganizerBookingsPage` | 需登录 + organizer |
| 12 | `/organizer/verify` | `VerifyPage` | 需登录 + organizer |
| 13 | `*` | `NotFound` | — |

---

## 4. 结论：目录范式

### 4.1 目录骨架

```
frontend/src/
├── assets/
├── common/
│   ├── api/          client.ts  codes.ts  messages.ts  types.ts  endpoints.ts  index.ts
│   ├── components/   AppShell  NavBar  RoleNav  NotFound  LoadingBlock  EmptyBlock  ErrorBlock  QrCode  form/
│   ├── router/       routes.ts  router.svelte.ts  RouteView.svelte  index.ts
│   ├── stores/       auth.svelte.ts
│   └── utils/
├── lib/
│   └── components/
│       └── ui/       ← shadcn 生成，严禁手改
├── pages/
│   ├── authentication/   LoginPage  RegisterPage
│   ├── events/           EventsPage  EventDetailPage
│   ├── seatmap/          SeatMapPage
│   ├── bookings/         BookingsPage  BookingCard
│   ├── tickets/          TicketPage  TicketByCodePage
│   └── organizer/        OrganizerEventsPage  OrganizerBookingsPage  VerifyPage
├── App.svelte
├── app.css
└── main.ts
```

### 4.2 命名与后缀

| 对象 | 规则 | 例 |
|---|---|---|
| 页面 | `XxxPage.svelte` | `BookingsPage.svelte` |
| 自定义组件 | PascalCase | `BookingCard.svelte` |
| runes store | **必须是 `.svelte.ts`** | `auth.svelte.ts` |
| 普通工具 / 常量 | camelCase `.ts` | `messages.ts`、`client.ts` |
| 路由表 | `routes.ts` | 路由常量与类型 |

### 4.3 导入与别名（红线）

1. 一律使用 `@/` 或 `$lib/` 别名，**禁止跨目录相对路径**；同目录内相对导入允许。
2. `@/* → src/*`；`$lib/* → src/lib/*`（`vite.config.ts` 与 `tsconfig.app.json` 已配置）。
3. 页面不得直接调用 `fetch`，一律走 `@/common/api`。
4. 页面不得直接读写 `localStorage`，一律走 `@/common/stores/auth.svelte`。

### 4.4 目录归属

| 目录 | 负责人 | 说明 |
|---|---|---|
| `common/{api,router,stores}/` + 壳类组件（`AppShell`、`NavBar`、`RoleNav`、`NotFound`、`QrCode`） | A | 应用壳、路由、请求层、会话、壳类组件 |
| `common/components/form/`、三态组件（`LoadingBlock`/`EmptyBlock`/`ErrorBlock`）、`app.css` 主题变量 | B | 表单与反馈组件、加载/空/错误态、主题与配色；S2-05 的 Tailwind 入口与 `@plugin` 由 A 一次性修复，主题变量与后续维护归 B |
| `pages/authentication/`、`pages/events/` | B | 登录注册、活动列表与详情 |
| `pages/seatmap/` | C | 3D 选座与预约提交 |
| `pages/bookings/`、`pages/tickets/` | A | 我的预约、取消、电子票 |
| `pages/organizer/` | F | 主办方后台与核验 |
| `lib/components/ui/` | 中立 | shadcn 生成件，**任何人不得手改**；需要封装时放 `common/components/` |

### 4.5 与 05 号文档的差异

05 号《六人分工方案》里写的是 `features/authentication/` 等目录名，属早期写法；03 号《前端开发规范》统一为 `pages/`。**以本文档为准：一律使用 `pages/`，不再新建 `features/`。**

### 4.6 新增页面的三步

1. 在 `pages/<模块>/` 新建 `XxxPage.svelte`。
2. 在 `common/router/routes.ts` 增加路由项（含 `requiresAuth` / `roles`）。
3. 需要接口时，在 `common/api/endpoints.ts` 增加路径函数，并在 `types.ts` 补类型。

---

## 5. 与其他契约的关系

| 关联 | 文档 | 说明 |
|---|---|---|
| 令牌存储与 401 | `docs/contracts/auth.md` | 守卫依赖 `auth.status`；401 跳转按 auth.md §7 |
| `/api` 前缀 | `docs/contracts/api.md` §1 | 前端 `baseURL="/api"`、`endpoints` 不带前缀；后端源码路由由 `APIRouter(prefix="/api")` 统一挂载，最终路径含 `/api`；代理不 rewrite |
| 状态枚举与中文标签 | `docs/contracts/enums.md` | `types.ts` 的字面量与 `STATUS_LABEL` 从这里同步 |
| 票号与二维码 | `docs/contracts/ticket-qr.md` | 票页与核验页的票号格式、二维码内容 |
| 接口路径常量 | `src/common/api/endpoints.ts` | 不含前缀，由请求客户端统一拼接 |

---

## 6. 验收自检（路由与应用壳落地时逐条执行）

| # | 操作 | 预期 |
|---|---|---|
| 1 | 地址栏输入 `#/events` | 显示活动列表占位页 |
| 2 | 输入 `#/events/9/seats` | 显示选座占位页，页面能读到 `id = 9` |
| 3 | 未登录输入 `#/bookings` | 跳 `#/login?next=%2Fbookings` |
| 4 | 输入 `#/no-such-page` | 显示 404 页 |
| 5 | 点浏览器后退 | 回到上一条路由 |
| 6 | 输入 `#/events//seats` | 视为不匹配 → 404 |
| 7 | 输入 `#/events/中文` | 参数正确解码，接口路径正确编码 |

---

## 7. 取消预约后的跨页一致性

取消预约会改变座位状态；“我的预约”“选座页”“电子票页”三处必须按本节保持一致，不能各自缓存旧结果。

### 7.1 取消成功后的跨页事件

取消接口返回 `code === 200` 后，由 `src/pages/bookings/cancelBooking.ts` 在**静默重拉列表之前**派发：

```ts
window.dispatchEvent(
  new CustomEvent("seatverse:booking-cancelled", {
    detail: {
      bookingId: id,
      eventId: booking.event.id,
      seatIds: booking.seats.map((seat) => seat.id),
    },
  }),
);
```

| 项 | 约定 |
|---|---|
| 事件名 | `seatverse:booking-cancelled` |
| `detail.bookingId` | 被取消的预约编号，integer |
| `detail.eventId` | 该预约对应的活动编号，integer |
| `detail.seatIds` | 该预约占用的座位编号数组，integer[] |
| 派发时机 | 取消成功响应到达后、静默重拉 `/bookings/me` 前 |
| 失败时 | 不派发；`409` / `401` / 网络失败均不派发 |
| 监听方 | 选座页；其它页面可忽略 |
| 作用域 | **仅当前标签页**的 `window`；跨标签页不会收到该事件 |

跨标签页不依赖这个事件：另一个窗口的选座页在重新进入或从后台切回时重新拉取动态状态（§7.2），以接口结果为准。

### 7.2 选座页的职责

| 场景 | 必须的行为 |
|---|---|
| 每次进入 `#/events/:id/seats` | 在 `onMount` 中重新请求 `GET /events/{id}/seats`，**不得复用上一次进入时的动态状态缓存** |
| 同页停留期间收到 `seatverse:booking-cancelled` | 若 `eventId` 与当前活动一致，重新请求动态座位状态；不一致则忽略 |
| 从后台切回该标签页（`visibilitychange` 变为 `visible`） | 重新请求动态座位状态，避免长时间停留后仍展示旧状态 |
| 本地已选集合 | 收到事件后，把 `detail.seatIds` 从本地已选中移除；若移除了当前选中项，提示“座位状态已更新，请重新选择” |
| 静态坐标 `GET /venues/{id}/seats` | 可在页面生命周期内缓存，坐标不随预约变化 |
| 动态状态 `GET /events/{id}/seats` | 不跨进入缓存；提交失败收到 `409` 时按既有规则刷新 |

- 选座页不得根据“我的预约列表里没有这条记录”推断座位可用，必须以动态座位接口为准。
- 选座页不得自己派发或伪造该事件，事件只由取消流程产生。

### 7.3 我的预约页的职责

1. 取消成功后先用响应 `payload` 就地更新该条：`status = "cancelled"`、`cancelledAt` 写入，按钮立即消失。
2. 随后静默重拉一次 `/bookings/me`；重拉期间不显示全页骨架，避免列表闪烁。
3. 重拉失败不回滚已显示的取消结果，只在列表顶部提示“列表刷新失败，请稍后重试”。
4. 重拉结果按 `id` 去重，不得出现重复卡片。

### 7.4 电子票页的职责

- 票状态以 `GET /bookings/{id}/ticket` 或 `GET /tickets/{code}` 的当前响应为准，不读取预约列表缓存。
- 已取消预约的票面标注“已失效”，核验时由后端返回 `409`。
- 已核验的票面标注“已核验”，不因取消事件改变。

### 7.5 验收

| # | 操作 | 预期 |
|---|---|---|
| 1 | 两个浏览器窗口并排：A 窗口取消预约，B 窗口刷新或切回该活动选座页 | 对应座位从“已预约”变“可选” |
| 2 | 在选座页同页停留，用 DevTools 派发同活动、同座位的 `seatverse:booking-cancelled` | 选座页重新请求动态状态并更新颜色 |
| 3 | 取消后切到“我的预约” | 该条显示“已取消”，取消按钮消失，无重复卡片 |
| 4 | 取消后直接打开该预约的电子票页 | 标注“已失效” |
| 5 | 取消请求失败（如重复取消 `409`） | 不派发事件，不误改座位颜色 |

跨标签页实时同步不在本契约范围；如后续需要，用 `storage` 或 `BroadcastChannel` 扩展，页面进入与切回时的重新拉取仍是兜底。

---

## 8. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-05 | 首版确定：hash 路由形态与 `pages/` 目录范式 | A |
| 2026-11-08 | 冻结：取消预约后的跨页事件与选座页刷新规则（§7）；澄清 `next` 取值口径（不含 `#`，与 `auth.md` §7.3 对齐），并在目录树补 `common/components/form/` | A |
