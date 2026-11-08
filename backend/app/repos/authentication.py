import sqlite3

from app.repos.database import (
    fetch_one_row,
    read_integer,
    read_text,
)
from app.types.authentication import UserRole, UserRow
from app.types.database import DatabaseConnection


def _read_role(row: sqlite3.Row) -> UserRole:
    value = read_text(row, "role")
    if value == "user" or value == "organizer":
        return value
    raise ValueError(f"Unknown role: {value!r}")


def _row_to_user(row: sqlite3.Row) -> UserRow:
    return UserRow(
        id=read_integer(row, "id"),
        name=read_text(row, "name"),
        email=read_text(row, "email"),
        password_hash=read_text(row, "password_hash"),
        role=_read_role(row),
        created_at=read_text(row, "created_at"),
    )


def find_user_by_email(connection: DatabaseConnection, email: str) -> UserRow | None:
    row = fetch_one_row(
        connection,
        "SELECT id, name, email, password_hash, role, created_at "
        "FROM users WHERE email = ?",
        (email,),
    )
    return None if row is None else _row_to_user(row)


def find_user_by_id(connection: DatabaseConnection, user_id: int) -> UserRow | None:
    row = fetch_one_row(
        connection,
        "SELECT id, name, email, password_hash, role, created_at "
        "FROM users WHERE id = ?",
        (user_id,),
    )
    return None if row is None else _row_to_user(row)
