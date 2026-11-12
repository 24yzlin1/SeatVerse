import sqlite3
from app.repos.database import (
    fetch_all_rows,
    fetch_one_row,
    get_connection,
    read_integer,
    read_text,
)
from app.types.venues import VenueRow


def _row_to_venue(row: sqlite3.Row) -> VenueRow:
    return VenueRow(
        id=read_integer(row, "id"),
        name=read_text(row, "name"),
        layout_config=read_text(row, "layout_config"),
        capacity=read_integer(row, "capacity"),
    )


def find_venue_by_id(venue_id: int) -> VenueRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, name, layout_config, capacity FROM venues WHERE id = ?",
            (venue_id,),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_venue(row)


def find_only_venue() -> VenueRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, name, layout_config, capacity FROM venues ORDER BY id ASC LIMIT 1",
        )
    finally:
        connection.close()
    return None if row is None else _row_to_venue(row)


def find_venue_by_name(name: str) -> VenueRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, name, layout_config, capacity FROM venues "
            "WHERE name = ? ORDER BY id ASC LIMIT 1",
            (name,),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_venue(row)


def insert_venue(name: str, layout_config: str, capacity: int) -> VenueRow:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO venues (name, layout_config, capacity) VALUES (?, ?, ?)",
            (name, layout_config, capacity),
        )
        connection.commit()
        last_row_id = cursor.lastrowid
        if last_row_id is None:
            raise RuntimeError("Failed to obtain inserted venue id")
        row = fetch_one_row(
            connection,
            "SELECT id, name, layout_config, capacity FROM venues WHERE id = ?",
            (last_row_id,),
        )
    finally:
        connection.close()
    if row is None:
        raise RuntimeError("Inserted venue row not found")
    return _row_to_venue(row)


def list_venues() -> list[VenueRow]:
    connection = get_connection()
    try:
        rows = fetch_all_rows(
            connection,
            "SELECT id, name, layout_config, capacity FROM venues ORDER BY id ASC",
        )
    finally:
        connection.close()
    return [_row_to_venue(row) for row in rows]
