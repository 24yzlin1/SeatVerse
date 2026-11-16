# SeatVerse 后端

FastAPI + SQLite，Python 3.13；依赖与任务由 uv / poe 管理。

## 目录

```text
backend/
├── app/
│   ├── types/      数据模型与响应结构
│   ├── repos/      数据库访问与迁移
│   ├── core/       业务用例
│   └── scope/      HTTP 入口（路由、参数校验）
├── main.py         应用入口、路由挂载与 CORS
├── scripts/        migrate.py、seed.py
└── pyproject.toml  uv 依赖与 poe 任务
```

## 环境变量

复制 `.env.example` 为 `.env`（`.env` 不入库）：

| 变量 | 作用 | 默认/示例 |
|---|---|---|
| `SEATVERSE_DATABASE_PATH` | SQLite 文件路径；相对路径按 `backend/` 解析 | `.db/data.db` |
| `SEATVERSE_JWT_SECRET` | JWT 签名密钥，至少 32 个字符 | `dev-only-change-me-0123456789abcdef` |

- 未设置数据库路径时使用 `backend/.db/data.db`，目录和文件已被 `.gitignore` 忽略。
- 生产环境必须显式设置 `SEATVERSE_JWT_SECRET`，不要使用示例值。

## 启动

```powershell
cd backend
uv sync
uv run poe dev
```

等价于 `uv run uvicorn main:app --reload`；启动后接口文档在 <http://localhost:8000/docs>。

## 路由与前缀

- 所有源码路由统一挂载在 `/api` 下（`APIRouter(prefix="/api")`），不使用 `--root-path`。
- 前端开发服务器把 `/api` 原样代理到后端，不做 rewrite。
- 生产网关不要剥掉 `/api` 前缀。
- CORS 允许 `http://localhost:5173` 与 `http://127.0.0.1:5173`。

## 常用任务

| 命令 | 作用 |
|---|---|
| `uv run poe dev` | 热重载启动 |
| `uv run poe start` | 直接启动 |
| `uv run poe check` | mypy 检查 `app`、`scripts`、`main.py` |
| `uv run poe test` | 运行 pytest；没有测试时退出码为 5 |
| `uv run poe migrate` | 执行数据库迁移 |
| `uv run poe seed` | 导入演示数据 |

## 种子数据

```powershell
uv run python -m scripts.seed --reset
```

运行后终端会打印演示账号；数据写入 `.db/`，不会进入仓库。
