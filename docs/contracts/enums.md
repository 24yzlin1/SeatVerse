# SeatVerse · 枚举与状态契约

> 状态：已冻结 ｜ 负责人：A ｜ 日期：2026-11-06
> 适用：前端 `types.ts` / `STATUS_LABEL` / 路由守卫，后端请求模型、业务规则与数据库状态写入
> 依据：01 号《项目策划书》§4、04 号《开发路线图》§3.5—3.7 / §5、05 号《六人分工方案》接口分工
> 说明：本文只冻结跨端共享的字符串字面量与流转规则，不规定数据库列类型、索引和内部版本号

---

## 1. 一句话结论

**所有跨端状态一律使用本文定义的小写英文字面量；中文只存在于前端标签映射与后端可展示的 `message` 中。后端负责校验与写入，前端不得创造、翻译或推断新的状态值。**

| 枚举 | 使用位置 | 字面量 | 中文标签 |
|---|---|---|---|
| `Role` | `user.role` | `user` / `organizer` | 普通用户 / 主办方 |
| `EventStatus` | `event.status` | `draft` / `published` / `closed` / `cancelled` | 草稿 / 已发布 / 已停止预约 / 已取消 |
| `EventSeatStatus` | `event_seats.status` | `available` / `locked` / `sold` | 可选 / 锁定 / 已预约 |
| `BookingStatus` | `booking.status` | `reserved` / `cancelled` / `used` | 待参加 / 已取消 / 已签到 |
| `TicketStatus` | `ticket.status` | `reserved` / `cancelled` / `used` | 待核验 / 已失效 / 已核验 |
| `SeatType` | `seat.seatType` | `standard` | 普通座 |

**统一约束**

1. 字面量**区分大小写**，只允许全小写；接口返回中文状态、拼音、首字母缩写均视为契约破坏。
2. `TicketStatus` 与对应 `BookingStatus` 使用同一套值；`ticket.status` 由预约状态与核验记录派生，不单独维护第二套可写状态。
3. 活动结束是**时间条件**（`now >= event.endTime`），不是状态值；本文不新增 `ended`。
4. `used` 只表示核验通过，**不表示活动结束**；活动结束后仍未被核验的预约保持 `reserved`。
5. `event_seats.version` 是后端并发控制字段，不进入本文契约，也不得由前端提交。

---

## 2. 逐项定义

### 2.1 `Role`

| 值 | 中文标签 | 权限摘要 |
|---|---|---|
| `user` | 普通用户 | 浏览活动、选座、预约、查看与取消自己的预约、出示自己的电子票 |
| `organizer` | 主办方 | 包含普通用户能力；创建与维护自己的活动、查看本场名单、核验自己活动的票 |

- 普通用户注册时不得提交 `role`，后端固定写入 `user`；主办方账号由种子数据预置。
- 前端的角色判断只用于界面显隐与路由分流，**权限最终以后端校验为准**。

### 2.2 `EventStatus`

| 值 | 中文标签 | 语义 | 是否接受新预约 |
|---|---|---|---|
| `draft` | 草稿 | 已创建但未发布，不对普通用户展示 | 否 |
| `published` | 已发布 | 正常展示，活动开始前可预约 | 是 |
| `closed` | 已停止预约 | 停止新预约，已有有效票与预约仍然有效 | 否 |
| `cancelled` | 已取消 | 活动取消，不再接受预约，已有票不得核验 | 否 |

- `closed` 与 `cancelled` 的区别：前者是正常停止报名，后者是活动本身取消。
- 活动是否“已结束”由 `endTime` 判断；`published` 但已过 `endTime` 的活动同样不接受预约。
- 01 号《项目策划书》生命周期里的“进行中”“已结束”是按 `startTime` / `endTime` 推导的**展示态**，不写入 `status`，派生规则见 §2.7；接口与数据库只使用上表四个字面量。“关闭预约”对应 `closed`，只停止新预约，不影响已有预约与核验。

### 2.3 `EventSeatStatus`

| 值 | 中文标签 | 语义 | 前端交互 |
|---|---|---|---|
| `available` | 可选 | 该场活动该座位当前可预约 | 可点击选中 |
| `locked` | 锁定 | 预留给后续实时锁座，第一版不写入 | 按不可选渲染 |
| `sold` | 已预约 | 已被有效预约占用 | 不可选 |

- 第一版只有 `available` 与 `sold` 会被业务写入；`locked` 仅为枚举占位，出现时按不可用处理。
- 座位颜色与可点击性必须按此枚举判断，不得用“本地已选”反推服务端状态。

### 2.4 `BookingStatus`

| 值 | 中文标签 | 语义 | 可取消 |
|---|---|---|---|
| `reserved` | 待参加 | 预约有效，尚未核验 | 是（须本人、活动开始前、未被核验） |
| `cancelled` | 已取消 | 用户已取消，关联座位恢复可选 | 否 |
| `used` | 已签到 | 主办方核验通过 | 否 |

- 预约列表接口返回全部状态，不按状态过滤；前端用 `$derived` 本地分组。
- 活动结束后不自动改写为 `used`；01 号 §4.2 的“已完成”由 §2.7 的 `BookingDisplayStatus.completed` 派生，存储值不变。

### 2.5 `TicketStatus`

| 值 | 中文标签 | 语义 | 二维码 |
|---|---|---|---|
| `reserved` | 待核验 | 票有效，尚未核验 | 正常展示 |
| `cancelled` | 已失效 | 对应预约已取消 | 可展示但标注失效，不得核验 |
| `used` | 已核验 | 已核验通过 | 可展示但标注已核验，不得重复核验 |

- `ticket.status` 是**派生字段**，不新增存储列：`booking.status === "cancelled"` → `cancelled`；票已核验（`verifiedAt` 非空）→ `used`；其余 → `reserved`。
- 派生读取与核验写入必须在同一事务语义下保持一致，不得出现“预约已取消、票面仍待核验”。
- 前端票面“已核验”徽标只看 `ticket.status === "used"`，不得自行用 `verifiedAt` 判断。
- 票号格式、二维码内容与核验接口见 `docs/contracts/ticket-qr.md`。

### 2.6 `SeatType`

| 值 | 中文标签 | 第一版是否会产生 |
|---|---|---|
| `standard` | 普通座 | 是 |

- 第一版只支持一种座位类型；后续新增类型只能追加字面量，不得改写 `standard` 的含义。
- 前端遇到未知 `seatType` 时按普通座样式渲染，并在控制台提示一次，不得崩溃。

### 2.7 展示状态（派生，不落库）

01 号 §4.2 用“进行中 / 已结束 / 已完成”描述生命周期。本契约不把这三个词写成存储列，而是由前端按时间与存储状态派生；派生规则固定如下，页面不得各自发明，也不得写回接口或数据库。

**`EventDisplayStatus`**（`EventStatus` + 当前时间）

| 值 | 中文标签 | 派生条件（按顺序取第一个命中项） |
|---|---|---|
| `cancelled` | 已取消 | `status === "cancelled"` |
| `ended` | 已结束 | `status` 为 `"published"` 或 `"closed"`，且 `now >= endTime` |
| `stopped` | 已停止预约 | `status === "closed"` 且 `now < endTime` |
| `ongoing` | 进行中 | `status === "published"` 或 `"closed"`，且 `startTime <= now < endTime` |
| `published` | 已发布 | `status === "published"` 且 `now < startTime` |
| `draft` | 草稿 | `status === "draft"` |

**`BookingDisplayStatus`**（`BookingStatus` + 活动时间）

| 值 | 中文标签 | 派生条件（按顺序取第一个命中项） |
|---|---|---|
| `cancelled` | 已取消 | `status === "cancelled"` |
| `used` | 已签到 | `status === "used"` |
| `completed` | 已完成 | `status === "reserved"` 且 `now >= event.endTime` |
| `reserved` | 待参加 | `status === "reserved"` 且 `now < event.endTime` |

- 派生顺序即优先级：已取消、已签到优先于时间判断；已签到的预约即使活动结束也显示“已签到”，不回退成“已完成”。
- 派生只用于展示、筛选与分组，**禁止**回写接口、数据库或 `localStorage`。
- 01 号 §4.2 的“活动结束后 → 已完成”由 `BookingDisplayStatus.completed` 承载；“进行中 / 已结束”由 `EventDisplayStatus.ongoing` / `ended` 承载。接口与数据库的存储值仍只有 §2.2 / §2.4 的字面量。

---

## 3. 状态流转

### 3.1 预约与电子票

```
reserved ──用户取消（本人、活动开始前、未核验）──► cancelled
    │
    └────主办方核验通过──────────────────────────► used

cancelled、used 为终态；不允许回退到 reserved
```

| 动作 | 前置条件 | 后置状态 | 关联变化 |
|---|---|---|---|
| 用户取消 | `status === reserved`、本人、`now < event.startTime` | `cancelled` | `cancelledAt` 写入；票面派生为 `cancelled`；关联座位回 `available` |
| 主办方核验 | `status === reserved`、主办方拥有该活动、活动未取消且未结束 | `used` | `verifiedAt` / `verifiedBy` 写入；票面派生为 `used`；座位保持 `sold` |
| 重复取消 | `status` 已是 `cancelled` 或 `used` | 不变 | 返回业务码 `409` |
| 重复核验 | `status === used` | 不变 | 返回业务码 `409` |

### 3.2 座位

```
available ──预约事务成功提交──► sold
sold ──────取消事务成功提交───► available
locked（第一版不进入业务流转，前端按不可选处理）
```

- 只有后端事务可以修改座位状态；前端颜色与本地已选集合都不是业务裁决。
- 多座位预约必须整体成功或整体回滚，不得出现部分 `sold`。

### 3.3 活动

```
draft ──发布──► published ──停止预约──► closed
  │                │                     │
  └────────────────┴─────────────────────┴──► cancelled
```

- 由活动主办方或后端业务规则触发；前端只读。
- `cancelled` 为终态；`closed` 不再接受新预约，但已有票仍可核验（活动未取消且未结束时）。
- 活动结束不写入新状态，统一用 `endTime` 判断。

---

## 4. 前端映射约定

### 4.1 唯一映射处

```ts
export const BOOKING_STATUS_LABEL = {
  reserved: "待参加",
  cancelled: "已取消",
  used: "已签到",
} as const;

export const TICKET_STATUS_LABEL = {
  reserved: "待核验",
  cancelled: "已失效",
  used: "已核验",
} as const;

export const EVENT_SEAT_STATUS_LABEL = {
  available: "可选",
  locked: "锁定",
  sold: "已预约",
} as const;

export const EVENT_STATUS_LABEL = {
  draft: "草稿",
  published: "已发布",
  closed: "已停止预约",
  cancelled: "已取消",
} as const;

// 展示态：按 §2.7 派生，不落库、不回传
export const EVENT_DISPLAY_STATUS_LABEL = {
  draft: "草稿",
  published: "已发布",
  ongoing: "进行中",
  ended: "已结束",
  stopped: "已停止预约",
  cancelled: "已取消",
} as const;

export const BOOKING_DISPLAY_STATUS_LABEL = {
  reserved: "待参加",
  completed: "已完成",
  cancelled: "已取消",
  used: "已签到",
} as const;

export const ROLE_LABEL = {
  user: "普通用户",
  organizer: "主办方",
} as const;
```

- 页面与组件不得各自维护一份中文标签表。
- 映射表使用 `Record<Status, string>` 或 `satisfies` 保证穷尽；新增枚举值时类型检查必须报错。
- 未知值兜底为 `未知状态（原值）`，只用于容错展示，不得把未知值当作任一已知状态处理。

### 4.2 禁止事项

1. 禁止在请求体、响应体、URL、`localStorage` 中写入中文状态。
2. 禁止前端把展示态（`已签到`、`待参加`、`已完成`）映射成存储状态后回传后端；回传只允许 `reserved` / `cancelled` / `used`。
3. 禁止用 `event_seats.status` 推断个人预约状态，也禁止用 `booking.status` 推断座位状态。
4. 禁止把活动结束时间当作预约状态；预约状态只由后端写入。
5. 禁止在页面中散落字符串比较，例如 `status === "已取消"`；一律引用常量或映射表。

---

## 5. 后端写入与校验约定

| 事项 | 约定 |
|---|---|
| 请求入参 | 状态只允许出现在约定的动作接口中，普通创建/更新请求不得直接提交任意状态 |
| 数据库 | 可写状态列存英文小写字面量；`ticket.status` 是派生字段，不落库 |
| 未知值 | 请求中出现未知状态一律 `400`；数据库中读到未知值按服务端错误处理，不得静默降级 |
| 并发 | 取消与核验在同一写事务内重查状态，使用条件更新；重复请求返回 `409` |
| 文案 | 中文文案只放在 `message` 与前端映射表，不写入状态列 |

---

## 6. 样例对照

| 样例文件 | 出现的状态 |
|---|---|
| `samples/bookings-me.ok.json` | `reserved`、`cancelled`；活动 `published`；座位 `standard` |
| `samples/booking-cancel.ok.json` | 取消结果 `cancelled` |
| `samples/ticket.ok.json` | 票与预约均为 `reserved` |
| `samples/error.409.json` | 重复取消的 `409` 文案 |

样例只用于字段与字面量对照，不作为真实数据导入。

---

## 7. 变更记录

| 日期 | 变更 | 负责人 |
|---|---|---|
| 2026-11-06 | 首版冻结：角色、活动、座位、预约、电子票、座位类型六组枚举与流转规则 | A |
| 2026-11-06 | 对齐 01 号 §4.2：补 §2.7 展示态（进行中 / 已结束 / 已完成），预约 `used` 中文标签改为“已签到” | A |
