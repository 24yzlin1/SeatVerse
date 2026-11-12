"""初始化 SeatVerse 的 SQLite 数据库并写入最小可用数据。

用法：
    uv run python -m scripts.migrate
    uv run python -m scripts.migrate --reset

行为：
1. 读取 backend/.env（存在时）里的 SEATVERSE_DATABASE_PATH；
2. 在对应路径创建数据库并执行 app/repos/migrations/*.sql；
3. 若不存在，写入一个演示主办方账号和一个预置场馆；
4. 重复执行不会重复插入；--reset 会先删除数据库文件再重建。
"""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import dotenv

from app.core.security import hash_password
from app.repos.authentication import find_user_by_email, insert_user
from app.repos.database import get_connection, get_database_path, run_migrations
from app.repos.venues import find_venue_by_name, insert_venue

_DEMO_ORGANIZER_NAME = "SeatVerse 主办方"
_DEMO_ORGANIZER_EMAIL = "organizer@seatverse.local"
_DEMO_ORGANIZER_PASSWORD = "Organizer123!"
_DEMO_VENUE_NAME = "学生活动中心·主报告厅"
_DEMO_VENUE_CAPACITY = 120
_DEMO_VENUE_LAYOUT = '{"rows": 10, "columns": 12}'


def _delete_database_files(database_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            candidate.unlink()
            print(f"Removed  : {candidate}")


def _seed_organizer() -> tuple[str, str]:
    """返回 (状态, 展示用邮箱)。已存在且角色不是 organizer 时直接报错。"""
    organizer = find_user_by_email(_DEMO_ORGANIZER_EMAIL)
    if organizer is None:
        insert_user(
            name=_DEMO_ORGANIZER_NAME,
            email=_DEMO_ORGANIZER_EMAIL,
            password_hash=hash_password(_DEMO_ORGANIZER_PASSWORD),
            role="organizer",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return "created", _DEMO_ORGANIZER_EMAIL
    if organizer.role != "organizer":
        raise RuntimeError(
            f"用户 {_DEMO_ORGANIZER_EMAIL} 已存在但不是 organizer，请先手动处理"
        )
    return "already exists", organizer.email


def _seed_venue() -> tuple[str, int]:
    venue = find_venue_by_name(_DEMO_VENUE_NAME)
    if venue is None:
        created = insert_venue(
            name=_DEMO_VENUE_NAME,
            layout_config=_DEMO_VENUE_LAYOUT,
            capacity=_DEMO_VENUE_CAPACITY,
        )
        return "created", created.id
    return "already exists", venue.id


def initialize_database(reset: bool = False) -> None:
    env_loaded = dotenv.load_dotenv()
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    if reset:
        _delete_database_files(database_path)

    run_migrations()
    organizer_state, organizer_email = _seed_organizer()
    venue_state, venue_id = _seed_venue()

    print(f"Env      : {'loaded' if env_loaded else 'not found, using defaults'}")
    print(f"Database : {database_path}")
    print("Schema   : migrations applied")
    print(f"Organizer: {organizer_email} ({organizer_state})")
    print(f"Venue    : {_DEMO_VENUE_NAME} id={venue_id} ({venue_state})")
    print(f"Demo login: {_DEMO_ORGANIZER_EMAIL} / {_DEMO_ORGANIZER_PASSWORD}")


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 SeatVerse SQLite 数据库")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="删除现有数据库文件（含 -wal/-shm）后重新初始化",
    )
    args = parser.parse_args()
    try:
        initialize_database(reset=bool(args.reset))
    except (RuntimeError, sqlite3.Error, OSError) as error:
        print(f"Migration failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
