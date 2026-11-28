import sqlite3
from app.repos.database import (
    fetch_one_row,
    get_connection,
    read_integer,
    read_text,
)
from app.types.ratings import RatingRow


def _row_to_rating(row: sqlite3.Row) -> RatingRow:
    return RatingRow(
        id=read_integer(row, "id"),
        event_id=read_integer(row, "event_id"),
        user_id=read_integer(row, "user_id"),
        score=read_integer(row, "score"),
        created_at=read_text(row, "created_at"),
        updated_at=read_text(row, "updated_at"),
    )


def upsert_rating(event_id: int, user_id: int, score: int, now: str) -> None:
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO event_ratings (event_id, user_id, score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id, user_id) 
            DO UPDATE SET score = excluded.score, updated_at = excluded.updated_at
            """,
            (event_id, user_id, score, now, now),
        )
        connection.commit()
    finally:
        connection.close()


def find_my_rating(event_id: int, user_id: int) -> RatingRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, event_id, user_id, score, created_at, updated_at "
            "FROM event_ratings WHERE event_id = ? AND user_id = ?",
            (event_id, user_id),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_rating(row)


def rating_summary(event_id: int) -> tuple[float | None, int]:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT ROUND(AVG(score), 1) AS average, COUNT(*) AS count "
            "FROM event_ratings WHERE event_id = ?",
            (event_id,),
        )
    finally:
        connection.close()
    
    if row is None:
        return None, 0
    
    avg_val = row["average"]
    average = float(avg_val) if avg_val is not None else None
    count = read_integer(row, "count")
    return average, count


def has_user_booked_event(event_id: int, user_id: int) -> bool:
    """检查用户是否对该活动有有效预约（reserved 或 used）"""
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT 1 AS has_booked FROM bookings "
            "WHERE event_id = ? AND user_id = ? AND status IN ('reserved', 'used') "
            "LIMIT 1",
            (event_id, user_id),
        )
    finally:
        connection.close()
    return row is not None