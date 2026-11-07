# SeatVerse

SeatVerse 是面向校园活动的 3D 场馆选座与预约平台：参与者浏览活动、进入 3D 场馆选座并预约，主办方发布活动、查看名单并扫码核验电子票。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Svelte 5 + Vite + TypeScript + Tailwind CSS + shadcn-svelte |
| 3D | Threlte / Three.js（选座页） |
| 后端 | Python 3.13 + FastAPI + SQLite |
| 工程 | uv（后端）、npm（前端）、poe（后端任务） |

## 目录结构

```text
SeatVerse/
├── backend/                 FastAPI 后端
│   ├── app/                 四层：types / repos / core / scope
│   ├── main.py              应用入口
│   └── pyproject.toml       uv 依赖与 poe 任务
├── frontend/                Svelte 5 + Vite 前端
│   └── src/                 App.svelte、app.css、common/、pages/、lib/
├── docs/
│   ├── collaboration.md     分支、提交信息与锁文件规范
│   └── contracts/           接口、登录态、枚举、电子票、前端路由契约
├── .github/                 PR 与 Issue 模板
└── README.md
```

## 启动三步

前置要求：

- Python 3.13 与 [uv](https://docs.astral.sh/uv/)
- Node.js 20+ 与 npm

```bash
# 1) 后端（终端 1）
cd backend && uv sync && uv run poe dev

# 2) 前端（终端 2，另开一个）
cd frontend && npm ci && npm run dev

# 3) 浏览器打开
# http://localhost:5173
```

启动后：

- 前端：<http://localhost:5173>
- 后端：<http://localhost:8000>
- 前端通过 Vite 代理访问后端，浏览器请求统一走 `/api/...`；后端源码路由统一挂载在 `/api` 下（`APIRouter(prefix="/api")`），代理原样转发、不 rewrite。

> 若 `npm ci` 因锁文件与 `package.json` 不同步而失败，先执行一次 `npm install` 重新生成锁文件，再按上面的命令启动。

## 检查入口

统一入口：

```bash
bash scripts/check.sh
```

> `scripts/check.sh` 在 S2-15 提供；在此之前使用等价命令：
>
> ```bash
> cd frontend && npm run check
> cd backend && uv run poe check
> ```

检查未通过不得合并；前端类型检查、后端 mypy 均要求零错误。

## 协作

- 分支模型、提交信息、锁文件规则与 PR 要求见 [docs/collaboration.md](docs/collaboration.md)。
- 接口与字段契约见 [docs/contracts/](docs/contracts/)；改接口前先改契约，再改实现。
- PR 模板与任务模板位于 `.github/`。
