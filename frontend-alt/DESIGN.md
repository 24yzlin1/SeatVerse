# SeatVerse 视觉设计规范

参照 `zyyl-alt` 实现整理，适用于 `frontend-alt` 全部页面。新增或修改 UI 必须遵循本规范。第 1 章是核心：每条禁止项都给出替代做法。

## 1. 禁止清单与做法

### 1.1 禁止常驻占位文案

**禁止**：界面出现「加载中…」「正在加载×××」「暂无×××」「尚未选择座位，请先……」「本地选择不锁座，提交后才确认预约」等常驻文字。

**做法**：

- 加载态是 **TODO 而非不做**：目前加载期间渲染空白，后续补骨架屏（`Skeleton`）；禁用的只是文案。
- 列表为空（`length === 0`）直接渲染空白，不渲染占位节点。
- 引导性信息改为**动作触发时**弹 toast。例如未登录时点「确认预约」：

```ts
async function confirmSeats() {
  if (!authentication.isLoggedIn) {
    toast.error("请先通过右上角账户入口登录，再确认座位");
    return;
  }
  const blockReason = disabledReason;
  if (blockReason) {
    toast.error(blockReason); // "预约未开始"等信息点击时才提示
    return;
  }
  // ...
}
```

### 1.2 禁止局部内嵌错误块

**禁止**：某一部分数据失败时，在页面局部渲染红色报错文字 + 「重试」按钮（牛皮癣）。

**做法**：失败只有两种呈现——

1. **页面级失败**（进不了页面）：整页 `Error` 组件，可带 `reloadCallback`。
2. **局部数据失败**：`toast.error(...)` 一条；同一失败原因连续出现**只提示一次**（防止 30 秒轮询刷屏）：

```ts
let errorReported = false;
// catch 内：
if (!errorReported) {
  errorReported = true;
  toast.error(message);
}
// 成功后重置：errorReported = false;
```

红色（destructive）只允许出现在徽章和 toast。

### 1.3 禁止成功横幅与完成态展示

**禁止**：预约成功后在页面顶部放横幅、完成态卡片、结果展示块（牛皮癣）。

**做法**：成功只弹一条 `toast.success(...)`；后续入口靠列表页/详情页导航，不在提交处堆结果。

```ts
if (session.state.completed?.event.id === eventId) {
  toast.success("预约成功");
}
```

### 1.4 禁止手动刷新按钮

**禁止**：「刷新座位」「刷新列表」等手动刷新按钮。

**做法**：数据页面用定时轮询 + 生命周期回源，无需用户手动刷新：

- 详情页预约/座位数据每 30 秒轮询；
- `visibilitychange` / 窗口回前台时刷新；
- 提交、取消等动作成功后主动重拉一次最新数据（保证状态反映用户最新一次提交）。

### 1.5 禁止同一信息多处重复展示

**禁止**：同一个数字/状态在页面上出现多处（如「已选 N 座」同时出现在状态行、确认栏标题、按钮文案三处）。

**做法**：一种信息只留**一处**。已选座位数量只在确认按钮上显示：`确认预约（{selectedSeats.length} 座）`；已选座位本身用底栏 chips 呈现（可点移除），不再配数量标题行。

### 1.6 禁止冗余导航按钮

**禁止**：页面内部再放「活动详情」「活动列表」「返回×××」等按钮——头部已有返回键、页面已有 Tab，重复入口是八宝粥。

**做法**：返回走顶部固定栏返回键，模块切换走 Tab 栏；票根页底栏只保留动作类图标按钮（活动详情跳转、取消预约），不放列表类入口。

### 1.7 禁止纯文字按钮泛滥

**禁止**：「查看本场座位」这类纯文字行内按钮；一个条目上堆多个文字按钮。

**做法**：行内动作一律图标按钮（`size="icon"` + `variant="secondary"` + `aria-label`/`title`），进行中换旋转 loader：

```svelte
<Button
  variant="secondary"
  size="icon"
  aria-label="取消预约"
  title="取消预约"
  disabled={cancelling !== null}
  onclick={(event) => {
    event.stopPropagation();
    void cancelBooking(booking);
  }}
>
  {#if cancelling === booking.id}
    <RiLoader4Line class="animate-spin" />
  {:else}
    <RiCloseCircleLine />
  {/if}
</Button>
```

纯文字按钮仅限：表单提交、加载更多等必要场景。

### 1.8 禁止重复 toast

**禁止**：一个动作成功弹两条通知（如组件内部弹一条、外层成功回调再叠一条 `toast.success("")`）。

**做法**：一个动作只在一处弹 toast；抽屉的 `succeedCallback` 只负责关闭抽屉。

### 1.9 禁止固定底栏样式与顶部不一致

**禁止**：底栏自带一套样式——不同的透明度、不同的模糊度、加上边框线（那根线）、换行堆叠布局。

**做法**：底栏与顶部固定栏样式完全一致，仅定位不同：

```
sticky bottom-0 z-9 h-14 px-6 flex items-center justify-between gap-4 bg-background/80 backdrop-blur-xs
```

无上边框；单行排布：左功能图标 + 右主按钮（`justify-between`），或全部靠右（`justify-end gap-2`）；中间内容横向滚动。

### 1.10 禁止展示组件发请求

**禁止**：纯展示组件里写 fetch/轮询/提交逻辑。

**做法**：容器/展示分层——容器（如 `SeatBooking.svelte`）承载加载、轮询、提交、竞态防护；展示组件（如 `SeatBookingSection.svelte`）只接 props 渲染。

### 1.11 禁止代码层坏味道

**禁止**：魔法缩写（`idx`、`cnt`、`auth` 等）；中文代码注释；布局组件埋在业务页面子目录。

**做法**：完整命名（`requestVersion`、`cancelling`、`authentication`）；注释用英文；布局组件放 `src/layout`，视图组件放对应业务模块 `components/` 子目录。

## 2. 主题与颜色

- Token 定义在 `src/app.css`：`--background`、`--foreground`、`--primary`、`--muted`、`--destructive`、`--border` 等，`.dark` 下提供暗色覆盖，`@theme inline` 映射为 Tailwind 颜色。
- 徽章变体：进行中状态（预约中）用 `variant="default"`，其余（已取消、已结束）用 `variant="destructive"`；列表项次要标签用 `variant="secondary"`。状态一律短标签（待参加 / 已签到 / 已取消）。

## 3. 布局骨架

- **顶部固定栏**：`sticky z-9 top-0 h-14 px-6 flex items-center gap-4 bg-background/80 backdrop-blur-xs`，含返回键与账户入口，无下边框。
- **页面骨架**：`src/layout/NavigationLayout.svelte` 提供 `panel` + `body` snippet；`panel` 渲染各模块 `Description.svelte`（`Empty.Root` + Header/Media/Title/Description 的模块介绍块），`body` 放筛选栏与列表。
- **筛选 Tab 栏**：`sticky top-14 h-14 px-6 flex items-center gap-4 bg-background/80 backdrop-blur-xs`，`Tabs.List` 放在 `grow overflow-x-scroll overflow-y-hidden` 容器内。
- **固定底栏**：见 1.9。

## 4. 列表页

```svelte
<Item.Root class={["click-link"]} onclick={() => push("/...")}>
  <Item.Content class={["overflow-hidden"]}>
    <Item.Title class={["line-clamp-1"]}>{标题}</Item.Title>
    <div class={["flex", "gap-2"]}>
      <Badge variant={...}>{状态短标签}</Badge>
      <Item.Description class={["line-clamp-1"]}>{次要信息}</Item.Description>
    </div>
  </Item.Content>
  <!-- 行内动作：只放必要的图标按钮，见 1.7 -->
</Item.Root>
```

- 整行可点击跳转；行内按钮必须 `event.stopPropagation()`。
- 分页：底部「加载更多预约」按钮，加载中不变文案、仅 `disabled`。
- 活动列表条目包含活动时间信息；列表筛选 Tab 见第 3 章。

## 5. 详情页与特殊区块

- 信息区统一 **muted 卡片**：`Item.Root variant="muted"`（同 zyyl 学校详情）；入场码区、核验页卡片同样式。
- 活动详情：「参与情况」图表（layerchart）+ 预约/座位数据 30 秒轮询。
- 入场码：二维码（uqr `renderSVG`）+ Code 39 条形码（jsbarcode，白底）+ 票号复制图标按钮（结果弹 toast）。
- 新建活动入口：sticky 筛选栏右侧图标按钮；新建抽屉只保留标题、必要输入、提交按钮。
- 竞态防护：请求带版本号/`LatestRequest`，账号或路由切换时丢弃旧响应。

## 6. 登录与账户

- 登录/注册合并为一个抽屉：`Drawer.Title` + `Tabs`（登录/注册）+ `Label + Input` + `Drawer.Footer` 单个提交按钮；成功后 `succeedCallback()` 关闭抽屉（见 1.8）。
- 已登录抽屉展示用户信息与登出；认证状态跨标签页同步（storage 事件）；401 统一清理会话。
- 受保护页未登录/无权限：`RequireAuthorize` 的 Empty 守卫块。

## 7. 反馈与状态速查

| 场景 | 呈现 |
| --- | --- |
| 页面级加载失败 | 整页 `Error`（可带 reloadCallback） |
| 局部数据失败 | `toast.error` 一条，同因只报一次 |
| 操作成功 | `toast.success` 一条 |
| 数据加载中 | TODO：暂空白占位，待补骨架屏；禁用「加载中…」文案 |
| 列表为空 | 空白，不渲染占位 |
| 未登录/无权限 | `RequireAuthorize` Empty 守卫块 |
| 需要引导的信息 | 动作触发时 toast，不做常驻提示 |

## 8. 图标

图标库 `remixicon-svelte`，统一 `Ri*Line` 线性后缀；注意个别名称以 remixicon 官方命名为准（如 `RiInformationLine` 而非 `RiInfoLine`）。
