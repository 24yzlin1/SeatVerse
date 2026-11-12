import sqlite3
from app.repos.database import (
    fetch_all_rows,
    fetch_one_row,
    get_connection,
    read_integer,
    read_text,
)
from app.types.events import ActivityStatus, EventRow, EventWithVenueRow

_EVENT_SELECT_COLUMNS = (
    "e.id, e.title, e.description, e.start_time, e.end_time, "
    "e.organizer_id, e.venue_id, e.status, e.created_at, "
    "v.name AS venue_name, v.capacity AS venue_capacity, "
    "u.name AS organizer_name"
)


def _read_status(row: sqlite3.Row) -> ActivityStatus:
    value = read_text(row, "status")
    if value == "draft":
        return "draft"
    if value == "published":
        return "published"
    if value == "closed":
        return "closed"
    if value == "cancelled":
        return "cancelled"
    raise ValueError(f"Unknown event status: {value!r}")


def _row_to_event(row: sqlite3.Row) -> EventRow:
    return EventRow(
        id=read_integer(row, "id"),
        title=read_text(row, "title"),
        description=read_text(row, "description"),
        start_time=read_text(row, "start_time"),
        end_time=read_text(row, "end_time"),
        organizer_id=read_integer(row, "organizer_id"),
        venue_id=read_integer(row, "venue_id"),
        status=_read_status(row),
        created_at=read_text(row, "created_at"),
    )


def _row_to_event_with_venue(row: sqlite3.Row) -> EventWithVenueRow:
    return EventWithVenueRow(
        event=_row_to_event(row),
        venue_name=read_text(row, "venue_name"),
        venue_capacity=read_integer(row, "venue_capacity"),
        organizer_name=read_text(row, "organizer_name"),
    )


def _escape_like_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_filters(
    keyword: str | None,
    status: ActivityStatus | None,
) -> tuple[str, list[object]]:
    conditions: list[str] = []
    parameters: list[object] = []
    if status is not None:
        conditions.append("e.status = ?")
        parameters.append(status)
    if keyword:
        escaped_keyword = _escape_like_pattern(keyword)
        conditions.append(
            "(e.title LIKE ? ESCAPE '\\' OR e.description LIKE ? ESCAPE '\\')"
        )
        keyword_parameter = f"%{escaped_keyword}%"
        parameters.append(keyword_parameter)
        parameters.append(keyword_parameter)
    where_clause = "" if not conditions else " WHERE " + " AND ".join(conditions)
    return where_clause, parameters


def find_events(
    keyword: str | None,
    status: ActivityStatus | None,
    limit: int,
    offset: int,
) -> list[EventWithVenueRow]:
    where_clause, parameters = _build_filters(keyword, status)
    sql = (
        f"SELECT {_EVENT_SELECT_COLUMNS} FROM events e "
        "JOIN venues v ON v.id = e.venue_id "
        "JOIN users u ON u.id = e.organizer_id"
        f"{where_clause} "
        "ORDER BY e.start_time ASC, e.id ASC "
        "LIMIT ? OFFSET ?"
    )
    page_parameters: list[object] = [*parameters, limit, offset]
    connection = get_connection()
    try:
        rows = fetch_all_rows(connection, sql, page_parameters)
    finally:
        connection.close()
    return [_row_to_event_with_venue(row) for row in rows]


def count_events(
    keyword: str | None,
    status: ActivityStatus | None,
) -> int:
    where_clause, parameters = _build_filters(keyword, status)
    sql = f"SELECT COUNT(*) AS total FROM events e{where_clause}"
    connection = get_connection()
    try:
        row = fetch_one_row(connection, sql, parameters)
    finally:
        connection.close()
    if row is None:
        return 0
    return read_integer(row, "total")


def find_event_by_id(event_id: int) -> EventWithVenueRow | None:
    sql = (
        f"SELECT {_EVENT_SELECT_COLUMNS} FROM events e "
        "JOIN venues v ON v.id = e.venue_id "
        "JOIN users u ON u.id = e.organizer_id "
        "WHERE e.id = ?"
    )
    connection = get_connection()
    try:
        row = fetch_one_row(connection, sql, (event_id,))
    finally:
        connection.close()
    return None if row is None else _row_to_event_with_venue(row)


def find_event_by_title(title: str) -> EventRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, title, description, start_time, end_time, organizer_id, "
            "venue_id, status, created_at FROM events "
            "WHERE title = ? ORDER BY id ASC LIMIT 1",
            (title,),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_event(row)


def insert_event(
    title: str,
    description: str,
    start_time: str,
    end_time: str,
    organizer_id: int,
    venue_id: int,
    status: ActivityStatus,
    created_at: str,
) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO events (title, description, start_time, end_time, "
            "organizer_id, venue_id, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                description,
                start_time,
                end_time,
                organizer_id,
                venue_id,
                status,
                created_at,
            ),
        )
        connection.commit()
        last_row_id = cursor.lastrowid
    finally:
        connection.close()
    if last_row_id is None:
        raise RuntimeError("Failed to obtain inserted event id")
    return last_row_id


def update_event_status(
    event_id: int,
    organizer_id: int,
    expected_status: ActivityStatus,
    target_status: ActivityStatus,
) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE events SET status = ? "
            "WHERE id = ? AND organizer_id = ? AND status = ?",
            (target_status, event_id, organizer_id, expected_status),
        )
        connection.commit()
        updated_row_count = cursor.rowcount
    finally:
        connection.close()
    return updated_row_count == 1
