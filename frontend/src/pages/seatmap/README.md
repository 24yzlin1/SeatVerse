# C-01 / C-02 / C-03 · 双视图场馆与座位选择

已交付类型、120 个固定座位、两场活动的动态状态，以及可旋转、缩放、重置和点击选座的 3D 场馆。平面选座保留且默认展开，与 3D 共用座位编号、坐标、状态和本地选择。全部座位数据来自本模块，不请求后端，不需要登录；预约确认与提交在 C-04—C-05 实施。

## 启动和入口

在 `frontend` 目录执行：

```powershell
npm ci
npm run dev
```

- 活动一：<http://localhost:5173/#/events/1001/seats>，102 座可选、18 座已预约。
- 活动二：<http://localhost:5173/#/events/1002/seats>，98 座可选、22 座已预约。
- 页面顶部可切换活动；浏览器后退、前进仍使用 A 的现有 hash 路由。
- 团队活动列表已接入真实接口；独立演示请直接访问以上模拟编号入口，无需启动后端。
- 未提供的编号（例如 `99999`）、非法编号（例如 `1001.0`）显示“未找到模拟活动”，不回退到另一场活动。

## 文件和挂载方式

- `types.ts`：静态座位、动态状态、活动／场馆、只读已选集合与场景交互回调。
- `mock-data.ts`：固定场馆与 120 座、两场活动、`getMockEvent(eventId)`。
- `SeatSelectionPage.svelte`：组合 3D、平面状态与坐标明细，可通过 `eventId: number` 和 `onEventChange: (eventId: number) => void` 独立挂载；仅进入本页时异步加载 3D 代码。
- `SeatScene.svelte`：画布容器、馆内／俯瞰切换、视角操作栏和初始化失败提示。
- `VenueScene.svelte`：画布内部的镜头、灯光、场馆、座位集合、方向标签与 OrbitControls。
- `SeatMesh.svelte`：挂载单座模型并响应显示状态，保留 `userData.seatId / row / number / label`，由父场景统一处理点击命中。
- `SceneLabel.svelte`：本地生成的舞台、入口与排号纹理，无外部模型／字体下载。
- `SeatPlan.svelte`：原生按钮组成的平面选座，直接按 X/Z 投影，可用鼠标、触摸或键盘选择。
- `SeatLegend.svelte`：两个视图共用的可选、已预约、本地已选与不可选图例。
- `selection.ts`：选择／取消、清空、刷新后过滤，以及业务状态优先的显示状态判定；纯逻辑不依赖 3D。
- `seat-layout.ts`：米制场馆、舞台、过道边界与平面投影，3D 和平面共用，不重新生成座位坐标。
- `seat-interaction.ts`：点击与旋转／多指手势的区分、可见场景的射线命中。
- `scene-model.ts`：真实 Three.js 模型、共享资源及镜头适配计算，可脱离浏览器测试。
- `SeatMapPage.svelte`：现有路由的薄接入层，读取 `router.params.id`，通过 `navigate()` 切换活动。
- `tests/seatmap.test.mjs` 与 `tests/seatmap-scene.test.mjs`（相对 `frontend/`）：数据契约、实际模型与镜头覆盖测试。
- `tests/seatmap-selection.test.mjs`、`seatmap-interaction.test.mjs`、`seatmap-visual.test.mjs`：共享选择、手势、状态材质和双视图坐标／命中一致性测试；统一执行 `npm run test:seatmap`。

按 `docs/contracts/frontend-arch.md` §4.5，文件放在 `pages/seatmap/`，替代旧工作计划建议的 `features/seat-selection/`。页面控件使用共享主题，礼堂内饰使用场景自身的材质。

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

待 A 确认：现有入口作为临时演示入口是否合适、真实活动编号传入方式。公共客户端现已由 A 落地在 `@/common/api`，C-07 应直接复用，页面不得自行 `fetch`、维护令牌或另起路由。

待 E 确认：

- 编号是否沿用契约的正整数，座位编号是否全局唯一，是否对应数据库 `seats.id`。
- `/venues/{id}/seats` 与 `/events/{id}/seats` 的完整 `payload` 形状（当前契约只冻结了接口索引）。
- 静态 `id` 与动态 `seatId` 的映射；数据库 `row_number`／`seat_number`／`seat_type` 对外是否统一为 `row`／`number`／`seatType`，与已有 `SeatBrief` 对齐。
- 坐标单位、右手系方向、场馆原点和座位基点；模拟约定不能视为后端已确认。
- 动态状态是否始终完整覆盖场馆座位；`available`／`sold`／`locked` 继续以 `enums.md` 为准，未知状态不得视为可选。

后续数据适配层负责加载静态坐标、活动状态和提交预约，复用 A 的客户端。路径函数不重复加入 `/api`；按响应体 `code` 判断成功／冲突，`409` 刷新状态。重新进入、切回前台和取消预约事件等刷新约定在 C-05／C-07 接入，不在当前固定数据预览中伪造真实请求。

## 依赖

依据 [Threlte 官方安装说明](https://threlte.xyz/docs/learn/getting-started/installation/)，本次只增加最小运行依赖 `@threlte/core@8.7.0`、`three@0.187.0`，以及开发依赖 `@types/three@0.187.0`。Core 的 peer 要求为 Svelte `>=5`、Three.js `>=0.172`，与当前工程匹配。

依赖已在 C-01 安装，C-02 直接复用，没有新增依赖或修改锁文件。OrbitControls 从 `three/addons/controls/OrbitControls.js` 导入，不需要 extras、物理或模型加载库。

## C-02 场馆与视角

- 使用 [Threlte Canvas](https://threlte.xyz/docs/reference/core/canvas/) 与现有 Three.js；画布跟随容器尺寸，桌面高度 420—540px，窄屏保持 420px。设备像素比限制为 1—1.75。
- 默认从后排中央过道看向音乐会舞台。四面墙、顶棚和后场双扇门围合观众厅，两侧设置吸音格栅和壁灯。台口有幕布、木质反声板和三角钢琴。120 座沿用 C-01 的坐标和编号。
- “全馆俯瞰”收起顶棚，随镜头转动隐藏靠近相机的一面或两面外墙。此视图显示排号和入口，可用于核对完整布局。
- 拖动或左右按钮旋转，滚轮、双指或加减按钮缩放。“重置视角”恢复当前视图。馆内视角限制旋转和距离，使镜头保持在厅内。窗口尺寸变化时按当前视图重新取景。
- 舞台聚光灯和向下投射的观众席照明分开布置，地面引导灯采用实例化网格。木纹和织物纹理本地生成，座椅、建筑和灯具共享材质。舞台和座椅投影使用一张 1024 × 1024 阴影贴图。
- 建筑与布灯改编自 Codrops 的影院示例。沿用其房间围护、侧墙格栅与壁灯、过道两侧琥珀色指示灯、台沿灯的设计，将弧形阶梯影院改为本项目的平地校园礼堂。使用现有的 WebGL 渲染器，并随前端构建分发原作者许可。[上游场馆源码](https://github.com/codrops/CinemaSeatPreview/blob/main/js/room.js) · [上游 MIT 许可](https://github.com/codrops/CinemaSeatPreview/blob/main/LICENSE) · [随附许可](../../../public/licenses/codrops-cinema-seat-preview.txt)

## C-03 双视图选座

- 空闲座可点击选中，再次点击取消；本地已选只保存在页面，不修改模拟占用状态，不表示已锁座。已预约、锁定、缺失或非法状态始终不可选，旧选择不会盖过新的业务状态。
- 页面持有唯一的选择集合，3D 和平面只通过同一个 `onSeatToggle(seatId)` 回调通知页面。切换模拟活动会清空选择；状态变化时过滤失效编号。
- **坐标保持一致**：3D 仍使用 `position = [seat.x, seat.y, seat.z]`；平面图按 `left = (x + 10) / 20`、`top = (z + 4) / 20` 投影为百分比。X 向右、Z 从舞台向后，平面舞台在上方；Y 为高度，不映射到平面。排号／座号仅作为标签，不参与重新摆位，120 个模拟坐标未改动。
- 两视图读取 `app.css` 的 `--seat-available`、`--seat-sold`、`--seat-selected`、`--seat-unavailable`；3D 在主题变化时更新共享状态材质，单座只切换材质引用，不修改其他座位。
- 指向 3D 座椅或聚焦平面按钮可查看完整排号、座号与状态；图例、本地已选数量、选择反馈和清空操作同时提供。平面图可折叠，窄屏可局部横向滚动，键盘 Tab / Enter / 空格均使用原生按钮行为。
- 3D 射线只检测可见座椅和建筑，不穿墙选座；拖动超过 6px、右键、双指、取消手势不触发选择。监听、主题观察器和悬停动画帧随场景卸载清理。

2026-11-18 C-03 本地验收（基于 `8249bdb`）：

- 座位／场景测试 **24/24** 通过，包含六类选择逻辑、非法状态／编号、不可变输入、非规则坐标投影、实际 120 座的平面／3D／点击编号一致性、单座材质隔离、可见建筑遮挡和手势判定。预约模块原有测试 **5/5** 通过。
- 全量类型检查 0 错误、0 警告，lint 通过，生产构建通过。场景 JS 约 803kB（gzip 207kB），沿用按需加载；现有 500kB 分包提示仍保留。
- 浏览器实际验证 3D 点击／再次点击取消，平面点击与 Enter 选择同步到 3D，已预约按钮禁用，拖动旋转不误选，清空选择，1001 / 1002 切换及返回后清空。离开选座页画布为 0，重新进入挂载完成后为 1。
- 390px 窗口下页面内容宽 375px，无页面整体横向溢出；平面区域宽 309px、内部宽 632px，可滚动并选择右侧座位。非法编号 `1001.0` 显示“未找到模拟活动”，返回后恢复正常。最终浏览器无 error / warn。
- 本模块和测试未发现 emoji。未新增依赖或修改锁文件；当前交付不包含预约提交，真实触屏双指手势尚待设备验收。

## 验收

在 `frontend` 目录运行：

```powershell
npm run test:seatmap
npm run check
npm exec -- eslint src/pages/seatmap tests/seatmap.test.mjs tests/seatmap-scene.test.mjs
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
6. 在窄屏检查顶部切换、3D 容器、平面图的局部横向滚动和概览区域；页面整体不应横向溢出。
7. 在馆内确认四周墙面、顶棚和舞台可见，再切换到“全馆俯瞰”。旋转、缩放后重置，确认 120 座及舞台恢复完整可见。切回馆内检查顶棚恢复。
8. 调整窗口宽度，确认场馆重新适配；进入登录页后返回，确认只有一个画布且视角控制正常。触屏手势需要在真实触屏设备另行检查。

2026-11-09 本地验收记录：

- 数据测试 4/4 通过，覆盖唯一编号／排座／坐标、完整状态关联、两场隔离、不可变样例和无效活动。
- 类型检查通过，0 错误、0 警告；本模块和测试的 ESLint 通过；生产构建通过。
- 全量 `npm run lint` 存在基线已有的 5 项 `prefer-const` 错误：`common/api/components/Empty.svelte` 两项、`ErrorState.svelte` 两项、`Loading.svelte` 一项。本次未修改这些公共组件。
- 浏览器已验证双活动切换、后退、离开后重新进入、未知活动恢复、120 行明细以及 390px 窄屏；控制台无警告／错误；演示不依赖后端。
- 尚未与 A／E 人工联调；3D 运行表现将在 C-02 验证。

2026-11-12 C-02 本地验收记录（基于 `93abcc2`）：

- 自动化测试 10/10 通过：原有 4 项数据测试，以及实际 120 个座椅的编号／坐标映射、模型互不重叠、地面／舞台／过道边界、三种画幅镜头覆盖和逐座射线命中。射线检查验证后续点击能对应到正确座位，不代表 C-03 已完成。
- `eslint src/pages/seatmap tests/seatmap.test.mjs tests/seatmap-scene.test.mjs` 通过；选座模块没有类型错误或 Svelte 警告，Node 配置的 `tsc` 通过。
- 生产构建成功。入口 JS 约 85kB，场景按需加载，JS 约 794kB（gzip 203kB）；3D 分包仍有 Vite 的 500kB 体积提示，未提高阈值或隐藏提示。
- 全量类型检查仍有基线的 2 个错误：`LoginPage.svelte` 的 `username` 不在 `LoginPayload` 中；`routes.ts` 挂载 `EventDetailPage` 时缺少必需 `id`。另有既存的 4 个 Svelte 警告（两处旧事件写法及活动卡片两处可访问性警告）。
- 全量 lint 仍有基线的 4 个错误：`RegisterPage` 未使用 `endpoints`；`EventDetailPage.id` 与 `EventsPage.pageSize` 应为 const；`EventsPage` 使用普通 `URLSearchParams`。没有改动这些队友页面，也没有加入忽略规则。以上 C-01 的 5 个公共组件错误属于历史记录，其修复此前已合并。
- 浏览器：1280px 桌面和 390px 窄屏显示完整舞台、过道和 120 座；鼠标拖动、滚轮缩放、旋转／缩放按钮、重置后继续操作通过。窄屏画布约 309 × 420px，页面宽 375px，没有整体横向溢出。
- 双活动计数与平面图、120 行明细保持一致；第二场 1 排 1 号为已预约。登录页离开后画布为 0 个，返回后为 1 个且控制正常；未知活动可恢复；最终页面控制台无 error／warn。
- 没有真实触屏设备测试、A／E 人工联调或预约行为验收；后续继续按 C-03—C-08 推进。
