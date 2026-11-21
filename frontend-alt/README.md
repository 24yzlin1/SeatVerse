# SeatVerse 当前主前端

Svelte 5 + Vite + TypeScript，保留新版界面，选座通过真实 FastAPI / SQLite 接口工作。

## 启动

先按 [后端说明](../backend/README.md) 启动 API，然后在本目录执行：

```powershell
npm ci
npm run dev
```

浏览器打开 `http://localhost:5173/#/events`，进入实际活动的“立即选座”页签，也可使用 `#/events/:id/seats`。登录使用右上角账户抽屉；普通用户可从仓库的后端开发种子账号登录。

请求通过 Vite 代理原样转发到 `/api`。正式页面没有模拟回退。使用既有业务数据库时不运行重置命令；首次空库按后端说明非重置导入种子数据。

## 检查

在仓库根目录运行 `scripts\check.cmd`（Windows）或 `bash scripts/check.sh`。统一检查现已指向本前端，包含类型、lint、构建、禁用项扫描和后端检查。

新增依赖时遵循 [协作规范](../docs/collaboration.md)，本轮未新增依赖或修改锁文件。生成的 shadcn UI 保持原样，不参与手写代码规则。

## 接口与业务

- [座位／预约接口和样例](../docs/contracts/seats-bookings.md)
- [C-07 选座实现与验收](src/pages/seatmap/README.md)
- 我的预约支持服务端状态筛选、继续加载及取消释放；详情页按活动查询本人预约，使用后端聚合座位统计。
- 成功展示服务端预约编号、座位与票号，并可进入真实电子票；关闭、结束和异常状态禁止预约。
- 本轮仅接入附件中 E／C-07 所需的预约筛选与座位统计，其余活动筛选、核验历史和主办方搜索提案仍为后续范围。
