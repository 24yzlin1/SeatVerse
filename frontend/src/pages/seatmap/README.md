# C-01 · 选座模块基础与模拟数据

本阶段交付类型、固定座位、两场活动的动态状态与平面数据预览。全部数据来自本模块，不请求后端，不需要登录。3D 场景、座位选择和预约提交分别在 C-02—C-05 实施。

## 启动和入口

在 `frontend` 目录执行：

```powershell
npm ci
npm run dev
```

- 活动一：<http://localhost:5173/#/events/1001/seats>，102 座可选、18 座已预约。
- 活动二：<http://localhost:5173/#/events/1002/seats>，98 座可选、22 座已预约。
- 页面顶部可切换活动；浏览器后退、前进仍使用 A 的现有 hash 路由。
- 活动列表目前是团队原有占位页，请直接访问以上入口。
- 未提供的编号（例如 `99999`）、非法编号（例如 `1001.0`）显示“未找到模拟活动”，不回退到另一场活动。

## 文件和挂载方式

- `types.ts`：静态座位、动态状态、活动／场馆、只读已选集合与场景交互回调。
- `mock-data.ts`：固定场馆与 120 座、两场活动、`getMockEvent(eventId)`。
- `SeatSelectionPage.svelte`：数据预览，可通过 `eventId: number` 和 `onEventChange: (eventId: number) => void` 独立挂载。
- `SeatMapPage.svelte`：现有路由的薄接入层，读取 `router.params.id`，通过 `navigate()` 切换活动。
- `tests/seatmap.test.mjs`（相对 `frontend/`）：数据契约自动化测试。

按 `docs/contracts/frontend-arch.md` §4.5，文件放在 `pages/seatmap/`，替代旧工作计划建议的 `features/seat-selection/`。不修改 App、公共路由表或共享主题；配色复用已有主题变量。

## 数据约定

1. 场馆编号 `1`；静态座位编号为正整数 `1—120`，每排 12 座、共 10 排。座位对象包含 `id`、`row`、`number`、`label`、`seatType`、`x`、`y`、`z`。
2. `label` 使用契约格式 `{row}排{number}号`，`seatType` 仅有 `standard`。编号与排座标识独立，正式接入时不能用数组下标生成业务编号。
3. 坐标是可重复的固定模拟布局，中央预留过道；单位为米，右手坐标系：X 向右、Y 向上，Z 从舞台指向后排。第一排 `z=1.8`，排距 `1.2`，座位基点 `y=0`；舞台可放在 `z=0` 前方。正式接入必须采用服务端坐标，不重新计算业务布局。
4. 动态记录只包含 `{ seatId, status }`，通过 `seatId === StaticSeat.id` 关联。活动由外层 `MockSeatEvent.event.id` 标识，每场都有完整的 120 条状态。
5. 状态使用冻结契约中的 `available`（可选）、`sold`（已预约）、`locked`（预留、不可选）；正常样例只写入前两种。缺失状态显示“状态未知，不可选”。
6. `SelectedSeatIds = ReadonlySet<SeatId>` 仅描述本地选择，不能写回动态状态或视为服务端锁座。`SeatSceneProps` 为后续场景预留数据和 `onSeatToggle`／`onSeatHover` 回调。
7. 两场的占用分布不同，例如座位 `1` 在 1001 场可选、1002 场已预约。模拟数据及每条记录均冻结，消费方应复制后再建立可写状态，避免重新进入时污染样例。
8. 活动日期为固定演示样例，采用带 `+08:00` 的 ISO 8601 字符串；页面显式按 UTC+8 展示，不受演示机时区影响。

## 与 A／E 的接入事项

已经依据 A 发布的冻结契约实现 `#/events/:id/seats` 和 `navigate()` 接入，未向队友发送消息或声称已取得人工确认。

待 A 确认：现有入口作为临时演示入口是否合适、真实活动编号传入方式，以及公共客户端落地后的统一导出。目前 `common/api` 尚无请求客户端；C-07 应使用 `@/common/api`，页面不得自行 `fetch`、维护令牌或另起路由。

待 E 确认：

- 编号是否沿用契约的正整数，座位编号是否全局唯一，是否对应数据库 `seats.id`。
- `/venues/{id}/seats` 与 `/events/{id}/seats` 的完整 `payload` 形状（当前契约只冻结了接口索引）。
- 静态 `id` 与动态 `seatId` 的映射；数据库 `row_number`／`seat_number`／`seat_type` 对外是否统一为 `row`／`number`／`seatType`，与已有 `SeatBrief` 对齐。
- 坐标单位、右手系方向、场馆原点和座位基点；模拟约定不能视为后端已确认。
- 动态状态是否始终完整覆盖场馆座位；`available`／`sold`／`locked` 继续以 `enums.md` 为准，未知状态不得视为可选。

后续数据适配层负责加载静态坐标、活动状态和提交预约，复用 A 的客户端。路径函数不重复加入 `/api`；按响应体 `code` 判断成功／冲突，`409` 刷新状态。重新进入、切回前台和取消预约事件等刷新约定在 C-05／C-07 接入，不在当前固定数据预览中伪造真实请求。

## 依赖

依据 [Threlte 官方安装说明](https://threlte.xyz/docs/learn/getting-started/installation/)，本次只增加最小运行依赖 `@threlte/core@8.7.0`、`three@0.187.0`，以及开发依赖 `@types/three@0.187.0`。Core 的 peer 要求为 Svelte `>=5`、Three.js `>=0.172`，与当前工程匹配。

这些依赖为 C-02 场景准备；本阶段不挂载 WebGL 画布。未提前引入 extras、物理或模型加载库。锁文件仅由一次 `npm install` 更新；新增 9 个包（含传递依赖），没有升级既有包。

## 验收

在 `frontend` 目录运行：

```powershell
npm run test:seatmap
npm run check
npm exec -- eslint src/pages/seatmap tests/seatmap.test.mjs
npm run lint
npm run build
```

数据测试复用工程已有 TypeScript 编译器和 Node 内置测试，无需新增测试依赖，支持团队的 Node 20+ 环境。

浏览器步骤：

1. 不启动后端，直接进入活动 1001，确认显示 120 座、102 可选／18 已预约。
2. 点击活动 1002，确认地址变为 `/events/1002/seats`、显示 98 可选／22 已预约，1 排 1 号从可选变为已预约。
3. 浏览器后退回 1001，确认计数和分布恢复；进入活动列表再后退，确认重新进入仍正确。
4. 展开“查看模拟座位数据”，确认共 120 行，首座编号 `1`、坐标 `(-7.1, 0, 1.8)`，可查看全部排座与状态。
5. 访问未知活动，确认显示提示，可点击上方任一活动恢复预览。
6. 在窄屏检查顶部切换、座位预览的局部横向滚动和概览区域；页面整体不应横向溢出。

2026-11-09 本地验收记录：

- 数据测试 4/4 通过，覆盖唯一编号／排座／坐标、完整状态关联、两场隔离、不可变样例和无效活动。
- 类型检查通过，0 错误、0 警告；本模块和测试的 ESLint 通过；生产构建通过。
- 全量 `npm run lint` 存在基线已有的 5 项 `prefer-const` 错误：`common/api/components/Empty.svelte` 两项、`ErrorState.svelte` 两项、`Loading.svelte` 一项。本次未修改这些公共组件。
- 浏览器已验证双活动切换、后退、离开后重新进入、未知活动恢复、120 行明细以及 390px 窄屏；控制台无警告／错误；演示不依赖后端。
- 尚未与 A／E 人工联调；3D 运行表现将在 C-02 验证。
