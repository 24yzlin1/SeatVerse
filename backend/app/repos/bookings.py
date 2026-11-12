"""预约与预约座位的数据库访问。

只写 SQL 与行映射：
- 写操作接收调用方连接，不 commit、不 close；
- 读操作自己开关连接，返回 typed 数据行。
"""

import sqlite3
from collections.abc import Sequence

from app.repos.database import (
    DatabaseConnection,
    fetch_all_rows,
    fetch_one_row,
    get_connection,
    read_integer,
    read_optional_text,
    read_text,
)
from app.types.bookings import (
    BookingEventRow,
    BookingListRow,
    BookingSeatBriefRow,
    BookingStatus,
    EventStatus,
)
from app.types.seats import SeatType


def _read_booking_status(value: str) -> BookingStatus:
    if value == "reserved":
        return "reserved"
    if value == "cancelled":
        return "cancelled"
    if value == "used":
        return "used"
    raise ValueError(f"Unknown booking status: {value!r}")


def _read_event_status(value: str) -> EventStatus:
    if value == "draft":
        return "draft"
    if value == "published":
        return "published"
    if value == "closed":
        return "closed"
    if value == "cancelled":
        return "cancelled"
    raise ValueError(f"Unknown event status: {value!r}")


def _read_seat_type(value: str) -> SeatType:
    if value == "standard":
        return "standard"
    raise ValueError(f"Unknown seat type: {value!r}")


def _row_to_booking_event(row: sqlite3.Row) -> BookingEventRow:
    return BookingEventRow(
        event_id=read_integer(row, "event_id"),
        status=_read_event_status(read_text(row, "status")),
        start_time=read_text(row, "start_time"),
        end_time=read_text(row, "end_time"),
        venue_id=read_integer(row, "venue_id"),
    )


def _row_to_booking_list(row: sqlite3.Row) -> BookingListRow:
    return BookingListRow(
        id=read_integer(row, "id"),
        status=_read_booking_status(read_text(row, "status")),
        created_at=read_text(row, "created_at"),
        cancelled_at=read_optional_text(row, "cancelled_at"),
        ticket_code=read_text(row, "ticket_code"),
        event_id=read_integer(row, "event_id"),
        event_title=read_text(row, "event_title"),
        event_status=_read_event_status(read_text(row, "event_status")),
        event_start_time=read_text(row, "event_start_time"),
        event_end_time=read_text(row, "event_end_time"),
        venue_id=read_integer(row, "venue_id"),
        venue_name=read_text(row, "venue_name"),
    )


def _row_to_booking_seat(row: sqlite3.Row) -> BookingSeatBriefRow:
    return BookingSeatBriefRow(
        booking_id=read_integer(row, "booking_id"),
        seat_id=read_integer(row, "seat_id"),
        row_number=read_integer(row, "row_number"),
        seat_number=read_integer(row, "seat_number"),
        seat_type=_read_seat_type(read_text(row, "seat_type")),
    )


def find_event_for_booking_in_transaction(
    connection: DatabaseConnection, event_id: int
) -> BookingEventRow | None:
    row = fetch_one_row(
        connection,
        "SELECT id AS event_id, status, start_time, end_time, venue_id "
        "FROM events WHERE id = ?",
        (event_id,),
    )
    return None if row is None else _row_to_booking_event(row)


def insert_booking(
    connection: DatabaseConnection,
    event_id: int,
    user_id: int,
    created_at: str,
) -> int:
    cursor = connection.execute(
        "INSERT INTO bookings (event_id, user_id, status, created_at) "
        "VALUES (?, ?, 'reserved', ?)",
        (event_id, user_id, created_at),
    )
    last_row_id = cursor.lastrowid
    if last_row_id is None:
        raise RuntimeError("Failed to obtain inserted booking id")
    return last_row_id


def insert_booking_seat(
    connection: DatabaseConnection,
    booking_id: int,
    event_id: int,
    seat_id: int,
) -> None:
    connection.execute(
        "INSERT INTO booking_seats (booking_id, event_id, seat_id, is_active) "
        "VALUES (?, ?, ?, 1)",
        (booking_id, event_id, seat_id),
    )


def find_booking_detail(booking_id: int, user_id: int) -> BookingListRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT b.id, b.status, b.created_at, b.cancelled_at, "
            "t.ticket_code, "
            "e.id AS event_id, e.title AS event_title, e.status AS event_status, "
            "e.start_time AS event_start_time, e.end_time AS event_end_time, "
            "v.id AS venue_id, v.name AS venue_name "
            "FROM bookings b "
            "JOIN events e ON e.id = b.event_id "
            "JOIN venues v ON v.id = e.venue_id "
            "JOIN tickets t ON t.booking_id = b.id "
            "WHERE b.id = ? AND b.user_id = ?",
            (booking_id, user_id),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_booking_list(row)


def list_booking_seats(booking_ids: Sequence[int]) -> list[BookingSeatBriefRow]:
    if not booking_ids:
        return []
    placeholders = ",".join("?" for _ in booking_ids)
    sql = (
        "SELECT bs.booking_id, s.id AS seat_id, s.row_number, s.seat_number, "
        "s.seat_type "
        "FROM booking_seats bs "
        "JOIN seats s ON s.id = bs.seat_id "
        f"WHERE bs.booking_id IN ({placeholders}) "
        "ORDER BY bs.booking_id, s.row_number, s.seat_number"
    )
    connection = get_connection()
    try:
        rows = fetch_all_rows(connection, sql, list(booking_ids))
    finally:
        connection.close()
    return [_row_to_booking_seat(row) for row in rows]
