"""座位与每场活动座位状态的数据库访问。

只写 SQL 与行映射，不做业务判断：
- `seats` 是场馆的固定座位与坐标，所有活动共用；
- `event_seats` 是某场活动中的动态状态，由发布流程或种子脚本初始化。
"""

import sqlite3

from app.repos.database import (
    DatabaseConnection,
    fetch_all_rows,
    fetch_one_row,
    get_connection,
    read_integer,
    read_real,
    read_text,
)
from app.types.seats import (
    EventSeatStateRow,
    EventSeatStatus,
    SeatRow,
    SeatType,
)

_SEAT_COLUMNS = (
    "id, venue_id, row_number, seat_number, x, y, z, seat_type"
)


def _read_seat_type(value: str) -> SeatType:
    if value == "standard":
        return "standard"
    raise ValueError(f"Unknown seat type: {value!r}")


def _read_event_seat_status(value: str) -> EventSeatStatus:
    if value == "available":
        return "available"
    if value == "locked":
        return "locked"
    if value == "sold":
        return "sold"
    raise ValueError(f"Unknown event seat status: {value!r}")


def _row_to_seat(row: sqlite3.Row) -> SeatRow:
    return SeatRow(
        id=read_integer(row, "id"),
        venue_id=read_integer(row, "venue_id"),
        row_number=read_integer(row, "row_number"),
        seat_number=read_integer(row, "seat_number"),
        x=read_real(row, "x"),
        y=read_real(row, "y"),
        z=read_real(row, "z"),
        seat_type=_read_seat_type(read_text(row, "seat_type")),
    )


def list_seats_by_venue(venue_id: int) -> list[SeatRow]:
    connection = get_connection()
    try:
        rows = fetch_all_rows(
            connection,
            f"SELECT {_SEAT_COLUMNS} FROM seats WHERE venue_id = ? "
            "ORDER BY row_number, seat_number",
            (venue_id,),
        )
    finally:
        connection.close()
    return [_row_to_seat(row) for row in rows]


def list_event_seats(event_id: int) -> list[EventSeatStateRow]:
    connection = get_connection()
    try:
        rows = fetch_all_rows(
            connection,
            "SELECT seat_id, status FROM event_seats "
            "WHERE event_id = ? ORDER BY seat_id",
            (event_id,),
        )
    finally:
        connection.close()
    return [
        EventSeatStateRow(
            seat_id=read_integer(row, "seat_id"),
            status=_read_event_seat_status(read_text(row, "status")),
        )
        for row in rows
    ]


def count_seats_by_venue(venue_id: int) -> int:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT COUNT(*) AS total FROM seats WHERE venue_id = ?",
            (venue_id,),
        )
    finally:
        connection.close()
    return 0 if row is None else read_integer(row, "total")


def insert_seat_if_missing(
    connection: DatabaseConnection,
    seat_id: int,
    venue_id: int,
    row_number: int,
    seat_number: int,
    x: float,
    y: float,
    z: float,
    seat_type: SeatType,
) -> bool:
    """插入固定座位；主键或 (venue,row,number) 已存在时跳过，返回是否真的插入。"""
    cursor = connection.execute(
        "INSERT INTO seats (id, venue_id, row_number, seat_number, x, y, z, seat_type) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT DO NOTHING",
        (seat_id, venue_id, row_number, seat_number, x, y, z, seat_type),
    )
    return cursor.rowcount == 1


def initialize_event_seats(
    connection: DatabaseConnection, event_id: int, venue_id: int
) -> int:
    """按场馆固定座位生成本场活动的座位状态；已存在的行跳过。

    接收调用方连接，不 commit、不 close；供发布事务和种子脚本复用。
    """
    cursor = connection.execute(
        "INSERT INTO event_seats (event_id, seat_id, status, version) "
        "SELECT ?, s.id, 'available', 0 FROM seats s WHERE s.venue_id = ? "
        "ON CONFLICT(event_id, seat_id) DO NOTHING",
        (event_id, venue_id),
    )
    return cursor.rowcount


def count_event_seats(event_id: int) -> int:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT COUNT(*) AS total FROM event_seats WHERE event_id = ?",
            (event_id,),
        )
    finally:
        connection.close()
    return 0 if row is None else read_integer(row, "total")
