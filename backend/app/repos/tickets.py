"""电子票与核验的数据访问。

只写 SQL 与行映射：
- 写操作接收调用方连接，不 commit、不 close；
- 查询同样接收调用方连接，由 core 层负责连接的生命周期（核验必须在同一事务内重查）。

`insert_ticket` 是 E 的预约事务调用 F 的唯一入口（05 号分工 §四“F → E”），
其余函数供 F 的票务查询、名单与核验使用。
"""

import sqlite3

from app.repos.database import (
    DatabaseConnection,
    fetch_all_rows,
    fetch_one_row,
    read_integer,
    read_optional_integer,
    read_optional_text,
    read_text,
)
from app.types.bookings import BookingStatus, EventStatus
from app.types.tickets import RosterRow, TicketDetailRow, TicketRow

_TICKET_DETAIL_COLUMNS = (
    "t.id AS ticket_id, t.booking_id AS booking_id, "
    "t.ticket_code AS ticket_code, t.verified_at AS verified_at, "
    "t.verified_by AS verified_by, "
    "b.status AS booking_status, b.created_at AS booking_created_at, "
    "b.user_id AS booking_user_id, "
    "e.id AS event_id, e.title AS event_title, e.status AS event_status, "
    "e.start_time AS event_start_time, e.end_time AS event_end_time, "
    "e.organizer_id AS event_organizer_id, "
    "v.id AS venue_id, v.name AS venue_name"
)

_TICKET_DETAIL_FROM = (
    " FROM tickets t "
    "JOIN bookings b ON b.id = t.booking_id "
    "JOIN events e ON e.id = b.event_id "
    "JOIN venues v ON v.id = e.venue_id"
)


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


def _row_to_ticket(row: sqlite3.Row) -> TicketRow:
    return TicketRow(
        id=read_integer(row, "id"),
        booking_id=read_integer(row, "booking_id"),
        ticket_code=read_text(row, "ticket_code"),
        verified_at=read_optional_text(row, "verified_at"),
        verified_by=read_optional_integer(row, "verified_by"),
    )


def _row_to_ticket_detail(row: sqlite3.Row) -> TicketDetailRow:
    return TicketDetailRow(
        ticket_id=read_integer(row, "ticket_id"),
        booking_id=read_integer(row, "booking_id"),
        ticket_code=read_text(row, "ticket_code"),
        verified_at=read_optional_text(row, "verified_at"),
        verified_by=read_optional_integer(row, "verified_by"),
        booking_status=_read_booking_status(read_text(row, "booking_status")),
        booking_created_at=read_text(row, "booking_created_at"),
        booking_user_id=read_integer(row, "booking_user_id"),
        event_id=read_integer(row, "event_id"),
        event_title=read_text(row, "event_title"),
        event_status=_read_event_status(read_text(row, "event_status")),
        event_start_time=read_text(row, "event_start_time"),
        event_end_time=read_text(row, "event_end_time"),
        event_organizer_id=read_integer(row, "event_organizer_id"),
        venue_id=read_integer(row, "venue_id"),
        venue_name=read_text(row, "venue_name"),
    )


def _row_to_roster(row: sqlite3.Row) -> RosterRow:
    return RosterRow(
        booking_id=read_integer(row, "booking_id"),
        booking_status=_read_booking_status(read_text(row, "booking_status")),
        created_at=read_text(row, "created_at"),
        cancelled_at=read_optional_text(row, "cancelled_at"),
        ticket_code=read_optional_text(row, "ticket_code"),
        user_id=read_integer(row, "user_id"),
        user_name=read_text(row, "user_name"),
        user_email=read_text(row, "user_email"),
        verified_at=read_optional_text(row, "verified_at"),
        verified_by=read_optional_integer(row, "verified_by"),
    )


def insert_ticket(
    connection: DatabaseConnection, booking_id: int, ticket_code: str
) -> TicketRow:
    """在调用方的预约事务内写入一张电子票，不自行提交。"""
    cursor = connection.execute(
        "INSERT INTO tickets (booking_id, ticket_code) VALUES (?, ?)",
        (booking_id, ticket_code),
    )
    last_row_id = cursor.lastrowid
    if last_row_id is None:
        raise RuntimeError("Failed to obtain inserted ticket id")
    row = fetch_one_row(
        connection,
        "SELECT id, booking_id, ticket_code, verified_at, verified_by "
        "FROM tickets WHERE id = ?",
        (last_row_id,),
    )
    if row is None:
        raise RuntimeError("Inserted ticket row not found")
    return _row_to_ticket(row)


def find_ticket_by_booking_id(
    connection: DatabaseConnection, booking_id: int
) -> TicketDetailRow | None:
    sql = (
        f"SELECT {_TICKET_DETAIL_COLUMNS}{_TICKET_DETAIL_FROM} "
        "WHERE t.booking_id = ?"
    )
    row = fetch_one_row(connection, sql, (booking_id,))
    return None if row is None else _row_to_ticket_detail(row)


def find_ticket_by_code(
    connection: DatabaseConnection, ticket_code: str
) -> TicketDetailRow | None:
    sql = (
        f"SELECT {_TICKET_DETAIL_COLUMNS}{_TICKET_DETAIL_FROM} "
        "WHERE t.ticket_code = ?"
    )
    row = fetch_one_row(connection, sql, (ticket_code,))
    return None if row is None else _row_to_ticket_detail(row)


def find_event_organizer_id(
    connection: DatabaseConnection, event_id: int
) -> int | None:
    row = fetch_one_row(
        connection,
        "SELECT organizer_id FROM events WHERE id = ?",
        (event_id,),
    )
    return None if row is None else read_integer(row, "organizer_id")


def list_event_roster(
    connection: DatabaseConnection,
    event_id: int,
    limit: int,
    offset: int,
) -> list[RosterRow]:
    sql = (
        "SELECT b.id AS booking_id, b.status AS booking_status, "
        "b.created_at AS created_at, b.cancelled_at AS cancelled_at, "
        "t.ticket_code AS ticket_code, t.verified_at AS verified_at, "
        "t.verified_by AS verified_by, "
        "u.id AS user_id, u.name AS user_name, u.email AS user_email "
        "FROM bookings b "
        "JOIN users u ON u.id = b.user_id "
        "LEFT JOIN tickets t ON t.booking_id = b.id "
        "WHERE b.event_id = ? "
        "ORDER BY b.created_at ASC, b.id ASC "
        "LIMIT ? OFFSET ?"
    )
    rows = fetch_all_rows(connection, sql, (event_id, limit, offset))
    return [_row_to_roster(row) for row in rows]


def count_event_roster(connection: DatabaseConnection, event_id: int) -> int:
    row = fetch_one_row(
        connection,
        "SELECT COUNT(*) AS total FROM bookings WHERE event_id = ?",
        (event_id,),
    )
    if row is None:
        return 0
    return read_integer(row, "total")


def mark_ticket_verified(
    connection: DatabaseConnection,
    ticket_id: int,
    verified_at: str,
    verified_by: int,
) -> bool:
    """条件更新：只有尚未核验的票才能写入核验信息（并发重复核验只会成功一次）。"""
    cursor = connection.execute(
        "UPDATE tickets SET verified_at = ?, verified_by = ? "
        "WHERE id = ? AND verified_at IS NULL",
        (verified_at, verified_by, ticket_id),
    )
    return cursor.rowcount == 1


def mark_booking_used(connection: DatabaseConnection, booking_id: int) -> bool:
    """条件更新：只有 `reserved` 的预约才能核验为 `used`。"""
    cursor = connection.execute(
        "UPDATE bookings SET status = 'used' WHERE id = ? AND status = 'reserved'",
        (booking_id,),
    )
    return cursor.rowcount == 1
