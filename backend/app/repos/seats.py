"""Database access for seats and per-event seat states.

Contains only SQL and row mapping, with no business judgment:
- `seats` holds a venue's fixed seats and coordinates, shared by all events;
- `event_seats` holds the dynamic state within a specific event, initialized
  by the publish flow or a seed script.
"""

import sqlite3

from app.repos.database import (
    DatabaseConnection,
    execute_update,
    fetch_all_rows,
    fetch_one_row,
    get_connection,
    read_integer,
    read_real,
    read_text,
)
from app.types.seats import (
    EventSeatRow,
    EventSeatStateRow,
    EventSeatStatus,
    SeatRow,
    SeatType,
    SeatStatisticsRow,
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


def event_seat_statistics(event_id: int) -> SeatStatisticsRow:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(status='sold'),0) AS sold, "
            "COALESCE(SUM(status='locked'),0) AS locked, "
            "COALESCE(SUM(status='available'),0) AS available "
            "FROM event_seats WHERE event_id=?",
            (event_id,),
        )
        if row is None:
            raise RuntimeError("Seat statistics query returned no row")
        return SeatStatisticsRow(
            total=read_integer(row, "total"), sold=read_integer(row, "sold"),
            locked=read_integer(row, "locked"), available=read_integer(row, "available"),
        )
    finally:
        connection.close()


def _row_to_event_seat(row: sqlite3.Row) -> EventSeatRow:
    return EventSeatRow(
        id=read_integer(row, "id"),
        event_id=read_integer(row, "event_id"),
        seat_id=read_integer(row, "seat_id"),
        status=_read_event_seat_status(read_text(row, "status")),
        version=read_integer(row, "version"),
    )


def find_event_seat_in_transaction(
    connection: DatabaseConnection, event_id: int, seat_id: int
) -> EventSeatRow | None:
    row = fetch_one_row(
        connection,
        "SELECT id, event_id, seat_id, status, version "
        "FROM event_seats WHERE event_id = ? AND seat_id = ?",
        (event_id, seat_id),
    )
    return None if row is None else _row_to_event_seat(row)


def mark_event_seat_sold(
    connection: DatabaseConnection, event_id: int, seat_id: int
) -> bool:
    """Conditional update: change to sold only while the seat is still available; returns whether the update matched."""
    updated = execute_update(
        connection,
        "UPDATE event_seats SET status = 'sold', version = version + 1 "
        "WHERE event_id = ? AND seat_id = ? AND status = 'available'",
        (event_id, seat_id),
    )
    return updated == 1


def release_event_seat(
    connection: DatabaseConnection, event_id: int, seat_id: int
) -> bool:
    """On booking cancellation, put a sold seat back to available; the conditional update prevents releasing the wrong seat."""
    updated = execute_update(
        connection,
        "UPDATE event_seats SET status = 'available', version = version + 1 "
        "WHERE event_id = ? AND seat_id = ? AND status = 'sold'",
        (event_id, seat_id),
    )
    return updated == 1


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
    """Insert a fixed seat; skipped when the primary key or (venue, row, number) already exists, and returns whether an insert actually happened."""
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
    """Generate this event's seat states from the venue's fixed seats; existing rows are skipped.

    Takes a caller-provided connection and neither commits nor closes it; reused by
    the publish transaction and seed scripts.
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
