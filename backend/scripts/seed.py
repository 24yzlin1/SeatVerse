"""导入 SeatVerse 的演示种子数据。

用法：
    uv run python -m scripts.seed --reset
    uv run python -m scripts.seed

数据来源（backend/scripts/data/）：
- users.jsonl  ：10 个普通用户（并发验收用）
- seats.jsonl  ：120 个固定座位，坐标与前端 mock-data.ts 一致
- events.jsonl ：4 场活动，覆盖 published / closed / draft 与“已结束”时间

行为：
1. 先执行 migrate（建表 + 演示主办方 + 预置场馆），--reset 时重建数据库；
2. 逐行读取 JSONL，已存在的用户/活动/座位跳过，可重复执行；
3. 为 published / closed 的活动初始化 event_seats，draft 不初始化。
"""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.security import hash_password
from app.repos.authentication import (
    count_users,
    find_organizer,
    find_user_by_email,
    insert_user,
)
from app.repos.database import (
    UniqueConstraintViolationError,
    get_connection,
    immediate_transaction,
)
from app.repos.events import count_events, find_event_by_title, insert_event
from app.repos.seats import (
    count_event_seats,
    count_seats_by_venue,
    initialize_event_seats,
    insert_seat_if_missing,
)
from app.repos.venues import find_only_venue
from app.types.events import ActivityStatus
from app.types.seats import SeatType
from scripts.migrate import initialize_database

_DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
_USERS_PATH = _DATA_DIRECTORY / "users.jsonl"
_SEATS_PATH = _DATA_DIRECTORY / "seats.jsonl"
_EVENTS_PATH = _DATA_DIRECTORY / "events.jsonl"


class SeedUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: str
    password: str
    role: Literal["user"] = "user"


class SeedSeat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    row: int
    number: int
    x: float
    y: float
    z: float
    seat_type: SeatType = "standard"


class SeedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    start_time: str
    end_time: str
    status: ActivityStatus


def _read_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _load_users() -> list[SeedUser]:
    return [SeedUser.model_validate_json(line) for line in _read_lines(_USERS_PATH)]


def _load_seats() -> list[SeedSeat]:
    return [SeedSeat.model_validate_json(line) for line in _read_lines(_SEATS_PATH)]


def _load_events() -> list[SeedEvent]:
    return [SeedEvent.model_validate_json(line) for line in _read_lines(_EVENTS_PATH)]


def _seed_users() -> tuple[int, int]:
    created = 0
    for item in _load_users():
        existing = find_user_by_email(item.email)
        if existing is not None:
            if existing.role != "user":
                raise RuntimeError(
                    f"用户 {item.email} 已存在且不是普通用户，请检查种子邮箱是否被占用"
                )
            continue
        insert_user(
            name=item.name,
            email=item.email,
            password_hash=hash_password(item.password),
            role=item.role,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        created += 1
    return created, count_users()


def _seed_seats(venue_id: int) -> tuple[int, int]:
    created = 0
    connection = get_connection()
    try:
        with immediate_transaction(connection):
            for item in _load_seats():
                inserted = insert_seat_if_missing(
                    connection=connection,
                    seat_id=item.id,
                    venue_id=venue_id,
                    row_number=item.row,
                    seat_number=item.number,
                    x=item.x,
                    y=item.y,
                    z=item.z,
                    seat_type=item.seat_type,
                )
                if inserted:
                    created += 1
    finally:
        connection.close()
    return created, count_seats_by_venue(venue_id)


def _seed_events(organizer_id: int, venue_id: int) -> tuple[int, int, int]:
    created = 0
    targets: list[tuple[int, ActivityStatus]] = []
    created_at = datetime.now(timezone.utc).isoformat()

    for item in _load_events():
        existing = find_event_by_title(item.title)
        if existing is None:
            event_id = insert_event(
                title=item.title,
                description=item.description,
                start_time=item.start_time,
                end_time=item.end_time,
                organizer_id=organizer_id,
                venue_id=venue_id,
                status=item.status,
                created_at=created_at,
            )
            effective_status = item.status
            created += 1
        else:
            event_id = existing.id
            effective_status = existing.status
        targets.append((event_id, effective_status))

    inserted_event_seats = 0
    connection = get_connection()
    try:
        with immediate_transaction(connection):
            for event_id, status in targets:
                if status == "published" or status == "closed":
                    inserted_event_seats += initialize_event_seats(
                        connection=connection,
                        event_id=event_id,
                        venue_id=venue_id,
                    )
    finally:
        connection.close()

    total_event_seats = sum(
        count_event_seats(event_id) for event_id, _ in targets
    )
    return created, inserted_event_seats, total_event_seats


def main() -> int:
    parser = argparse.ArgumentParser(description="导入 SeatVerse 演示种子数据")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置数据库（含 migrate 创建的主办方与场馆）后重新导入",
    )
    args = parser.parse_args()

    try:
        initialize_database(reset=bool(args.reset))
        organizer = find_organizer()
        if organizer is None:
            raise RuntimeError("未找到主办方账号，请先运行 scripts.migrate")
        venue = find_only_venue()
        if venue is None:
            raise RuntimeError("未找到预置场馆，请先运行 scripts.migrate")

        users_created, users_total = _seed_users()
        seats_created, seats_total = _seed_seats(venue.id)
        events_created, event_seats_created, event_seats_total = _seed_events(
            organizer.id, venue.id
        )
    except (
        RuntimeError,
        OSError,
        ValueError,
        sqlite3.Error,
        UniqueConstraintViolationError,
    ) as error:
        print(f"Seed failed: {error}")
        return 1

    print(f"Users      : {users_created} created, {users_total} total")
    print(f"Seats      : {seats_created} created, {seats_total} total")
    print(f"Events     : {events_created} created, {count_events(None, None)} total")
    print(
        f"Event seats: {event_seats_created} created, {event_seats_total} total"
    )
    print("Demo users : user01@seatverse.local ... user10@seatverse.local")
    print("Demo password: User12345!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
