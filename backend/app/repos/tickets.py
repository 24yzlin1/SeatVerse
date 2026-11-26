"""Database access for e-tickets and verification.

Contains only SQL and row mapping:
- Write operations take a caller-provided connection and neither commit nor close it;
- Queries likewise take a caller-provided connection, with the core layer owning the
  connection lifecycle (verification must re-read within the same transaction).

`insert_ticket` is the only entry point through which E's booking transaction calls F
(work-split doc 05, §4 "F → E"); the remaining functions serve F's ticket queries,
rosters, and verification.
"""

import sqlite3
from collections.abc import Sequence

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
from app.types.tickets import (
    RosterRow,
    RosterSummaryRow,
    TicketDetailRow,
    TicketRow,
)

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
        event_id=read_integer(row, "event_id"),
        event_title=read_text(row, "event_title"),
        event_status=_read_event_status(read_text(row, "event_status")),
        event_start_time=read_text(row, "event_start_time"),
        event_end_time=read_text(row, "event_end_time"),
        venue_id=read_integer(row, "venue_id"),
        venue_name=read_text(row, "venue_name"),
    )


def insert_ticket(
    connection: DatabaseConnection, booking_id: int, ticket_code: str
) -> TicketRow:
    """Insert an e-ticket inside the caller's booking transaction without committing on its own."""
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
    statuses: Sequence[BookingStatus] = (),
) -> list[RosterRow]:
    status_sql = ""
    parameters: list[object] = [event_id]
    if statuses:
        status_sql = " AND b.status IN (" + ",".join("?" for _ in statuses) + ")"
        parameters.extend(statuses)
    sql = (
        "SELECT b.id AS booking_id, b.status AS booking_status, "
        "b.created_at AS created_at, b.cancelled_at AS cancelled_at, "
        "t.ticket_code AS ticket_code, t.verified_at AS verified_at, "
        "t.verified_by AS verified_by, "
        "u.id AS user_id, u.name AS user_name, u.email AS user_email, "
        "e.id AS event_id, e.title AS event_title, e.status AS event_status, "
        "e.start_time AS event_start_time, e.end_time AS event_end_time, "
        "v.id AS venue_id, v.name AS venue_name "
        "FROM bookings b "
        "JOIN users u ON u.id = b.user_id "
        "JOIN events e ON e.id = b.event_id "
        "JOIN venues v ON v.id = e.venue_id "
        "LEFT JOIN tickets t ON t.booking_id = b.id "
        "WHERE b.event_id = ?"
        f"{status_sql} "
        "ORDER BY b.created_at ASC, b.id ASC "
        "LIMIT ? OFFSET ?"
    )
    rows = fetch_all_rows(connection, sql, [*parameters, limit, offset])
    return [_row_to_roster(row) for row in rows]


def count_event_roster(
    connection: DatabaseConnection,
    event_id: int,
    statuses: Sequence[BookingStatus] = (),
) -> int:
    status_sql = ""
    parameters: list[object] = [event_id]
    if statuses:
        status_sql = " AND b.status IN (" + ",".join("?" for _ in statuses) + ")"
        parameters.extend(statuses)
    row = fetch_one_row(
        connection,
        "SELECT COUNT(*) AS total FROM bookings b "
        "WHERE b.event_id = ?" + status_sql,
        parameters,
    )
    if row is None:
        return 0
    return read_integer(row, "total")


def event_roster_summary(
    connection: DatabaseConnection, event_id: int
) -> RosterSummaryRow:
    """Count this event's bookings by status; the roster page no longer tallies check-in progress item by item in the frontend."""
    row = fetch_one_row(
        connection,
        "SELECT COUNT(*) AS total, "
        "COALESCE(SUM(status='reserved'),0) AS reserved, "
        "COALESCE(SUM(status='used'),0) AS checked_in, "
        "COALESCE(SUM(status='cancelled'),0) AS cancelled "
        "FROM bookings WHERE event_id = ?",
        (event_id,),
    )
    if row is None:
        raise RuntimeError("Roster summary query returned no row")
    return RosterSummaryRow(
        total=read_integer(row, "total"),
        reserved=read_integer(row, "reserved"),
        checked_in=read_integer(row, "checked_in"),
        cancelled=read_integer(row, "cancelled"),
    )


def mark_ticket_verified(
    connection: DatabaseConnection,
    ticket_id: int,
    verified_at: str,
    verified_by: int,
) -> bool:
    """Conditional update: only tickets not yet verified can have verification info written (concurrent duplicate verifications succeed only once)."""
    cursor = connection.execute(
        "UPDATE tickets SET verified_at = ?, verified_by = ? "
        "WHERE id = ? AND verified_at IS NULL",
        (verified_at, verified_by, ticket_id),
    )
    return cursor.rowcount == 1


def mark_booking_used(connection: DatabaseConnection, booking_id: int) -> bool:
    """Conditional update: only a `reserved` booking can be verified into `used`."""
    cursor = connection.execute(
        "UPDATE bookings SET status = 'used' WHERE id = ? AND status = 'reserved'",
        (booking_id,),
    )
    return cursor.rowcount == 1


def _escape_like_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_verified_tickets(
    connection: DatabaseConnection,
    organizer_id: int,
    event_id: int | None,
    verified_from: str | None,
    verified_to: str | None,
    limit: int,
    offset: int,
) -> list[TicketDetailRow]:
    """Verification history: verified tickets (an organizer sees only records for their own events).

    The time range is given as optional ISO 8601 strings; the caller (core) is
    responsible for normalizing the inputs to the same UTC ISO format as
    `verified_at`, ensuring correct string comparison.
    """
    conditions = ["t.verified_at IS NOT NULL", "e.organizer_id = ?"]
    parameters: list[object] = [organizer_id]
    if event_id is not None:
        conditions.append("b.event_id = ?")
        parameters.append(event_id)
    if verified_from is not None:
        conditions.append("t.verified_at >= ?")
        parameters.append(verified_from)
    if verified_to is not None:
        conditions.append("t.verified_at <= ?")
        parameters.append(verified_to)
    where = " WHERE " + " AND ".join(conditions)
    sql = (
        f"SELECT {_TICKET_DETAIL_COLUMNS}{_TICKET_DETAIL_FROM}"
        f"{where} "
        "ORDER BY t.verified_at DESC, b.id DESC "
        "LIMIT ? OFFSET ?"
    )
    rows = fetch_all_rows(connection, sql, [*parameters, limit, offset])
    return [_row_to_ticket_detail(row) for row in rows]


def count_verified_tickets(
    connection: DatabaseConnection,
    organizer_id: int,
    event_id: int | None,
    verified_from: str | None,
    verified_to: str | None,
) -> int:
    conditions = ["t.verified_at IS NOT NULL", "e.organizer_id = ?"]
    parameters: list[object] = [organizer_id]
    if event_id is not None:
        conditions.append("b.event_id = ?")
        parameters.append(event_id)
    if verified_from is not None:
        conditions.append("t.verified_at >= ?")
        parameters.append(verified_from)
    if verified_to is not None:
        conditions.append("t.verified_at <= ?")
        parameters.append(verified_to)
    where = " WHERE " + " AND ".join(conditions)
    sql = (
        "SELECT COUNT(*) AS total "
        "FROM tickets t "
        "JOIN bookings b ON b.id = t.booking_id "
        "JOIN events e ON e.id = b.event_id"
        f"{where}"
    )
    row = fetch_one_row(connection, sql, parameters)
    if row is None:
        return 0
    return read_integer(row, "total")


def list_bookings_by_username(
    connection: DatabaseConnection,
    keyword: str,
    limit: int,
    offset: int,
) -> list[RosterRow]:
    """Fuzzy-match bookings by username (organizer view), newest first.

    Like the roster query, returns booking + user + event + ticket verification
    info, so the frontend can show "which events an attendee signed up for".
    """
    escaped = _escape_like_pattern(keyword)
    pattern = f"%{escaped}%"
    sql = (
        "SELECT b.id AS booking_id, b.status AS booking_status, "
        "b.created_at AS created_at, b.cancelled_at AS cancelled_at, "
        "t.ticket_code AS ticket_code, t.verified_at AS verified_at, "
        "t.verified_by AS verified_by, "
        "u.id AS user_id, u.name AS user_name, u.email AS user_email, "
        "e.id AS event_id, e.title AS event_title, e.status AS event_status, "
        "e.start_time AS event_start_time, e.end_time AS event_end_time, "
        "v.id AS venue_id, v.name AS venue_name "
        "FROM bookings b "
        "JOIN users u ON u.id = b.user_id "
        "JOIN events e ON e.id = b.event_id "
        "JOIN venues v ON v.id = e.venue_id "
        "LEFT JOIN tickets t ON t.booking_id = b.id "
        "WHERE u.name LIKE ? ESCAPE '\\' "
        "ORDER BY b.created_at DESC, b.id DESC "
        "LIMIT ? OFFSET ?"
    )
    rows = fetch_all_rows(connection, sql, (pattern, limit, offset))
    return [_row_to_roster(row) for row in rows]


def count_bookings_by_username(
    connection: DatabaseConnection,
    keyword: str,
) -> int:
    escaped = _escape_like_pattern(keyword)
    pattern = f"%{escaped}%"
    row = fetch_one_row(
        connection,
        "SELECT COUNT(*) AS total FROM bookings b "
        "JOIN users u ON u.id = b.user_id "
        "WHERE u.name LIKE ? ESCAPE '\\'",
        (pattern,),
    )
    if row is None:
        return 0
    return read_integer(row, "total")
