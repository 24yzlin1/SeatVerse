# SeatVerse 前端

SeatVerse 是面向校园活动的 3D 场馆选座与预约平台，本目录是 Svelte 5 + Vite 前端。

## 技术栈

- Svelte 5 + Vite + TypeScript
- Tailwind CSS 4 + shadcn-svelte
- 3D 选座：Threlte + Three.js

## 环境要求

- Node.js 20+、npm
- Windows PowerShell 默认禁止执行 `npm.ps1`，请统一使用 `npm.cmd`

## 安装与启动

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

打开 <http://localhost:5173>。后端默认在 <http://localhost:8000>，需另行启动（见仓库根 README）。

## 代理与环境变量

- 浏览器里的接口请求统一走 `/api`，Vite 把 `/api` 代理到 `http://localhost:8000`，原样转发、不 rewrite。
- 需要指向其他后端时设置 `VITE_API_BASE`（默认 `/api`）。

## 检查

```powershell
npm.cmd run check        # svelte-check
npm.cmd run lint         # eslint
npm.cmd run build        # 生产构建
npm.cmd run test:seatmap # 选座数据与 3D 模型测试
```

仓库根还提供一键检查入口（见根 README「检查入口」）；脚本未就绪时以以上命令为准，全绿再合并。

## 目录

```text
src/
├── common/        api、components、router、stores、utils
├── pages/         按业务划分的页面
├── lib/           shadcn 生成的 UI（不手改）与工具函数
├── App.svelte     应用壳 + 路由出口
└── main.ts        挂载入口
```

## 约定

- 页面放 `src/pages/`，公共层放 `src/common/`；`src/lib/components/ui/` 由 shadcn 生成，不要手改。
- 接口类型与路径统一在 `src/common/api/`，页面不直接 `fetch`。
