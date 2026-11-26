"""Initialize the SeatVerse SQLite database and write minimal usable data.

Usage:
    uv run python -m scripts.migrate
    uv run python -m scripts.migrate --reset

Behavior:
1. Read SEATVERSE_DATABASE_PATH from backend/.env (when present);
2. Create the database at that path and execute app/repos/migrations/*.sql;
3. If missing, write one demo organizer account and one preset venue;
4. Re-running does not insert duplicates; --reset deletes the database file
   first and rebuilds.
"""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import dotenv

from app.core.security import hash_password
from app.repos.authentication import find_user_by_email, insert_user
from app.repos.database import get_database_path, run_migrations
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
    """Return (state, display email). Raise directly if the user exists but is
    not an organizer."""
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
            f"User {_DEMO_ORGANIZER_EMAIL} already exists but is not an organizer; please handle it manually first"
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
    parser = argparse.ArgumentParser(description="Initialize the SeatVerse SQLite database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing database files (including -wal/-shm) before re-initializing",
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
