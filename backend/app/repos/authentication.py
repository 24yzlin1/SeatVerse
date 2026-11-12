import sqlite3
from app.repos.database import (
    UniqueConstraintViolationError,
    fetch_one_row,
    get_connection,
    read_integer,
    read_text,
)
from app.types.authentication import UserRole, UserRow


def _read_role(row: sqlite3.Row) -> UserRole:
    value = read_text(row, "role")
    if value == "user":
        return "user"
    if value == "organizer":
        return "organizer"
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


def find_user_by_email(email: str) -> UserRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, name, email, password_hash, role, created_at "
            "FROM users WHERE email = ?",
            (email,),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_user(row)


def find_user_by_id(user_id: int) -> UserRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, name, email, password_hash, role, created_at "
            "FROM users WHERE id = ?",
            (user_id,),
        )
    finally:
        connection.close()
    return None if row is None else _row_to_user(row)


def find_organizer() -> UserRow | None:
    connection = get_connection()
    try:
        row = fetch_one_row(
            connection,
            "SELECT id, name, email, password_hash, role, created_at "
            "FROM users WHERE role = 'organizer' ORDER BY id ASC LIMIT 1",
        )
    finally:
        connection.close()
    return None if row is None else _row_to_user(row)


def count_users() -> int:
    connection = get_connection()
    try:
        row = fetch_one_row(connection, "SELECT COUNT(*) AS total FROM users")
    finally:
        connection.close()
    return 0 if row is None else read_integer(row, "total")


def insert_user(
    name: str, email: str, password_hash: str, role: UserRole, created_at: str
) -> UserRow:
    connection = get_connection()
    try:
        try:
            cursor = connection.execute(
                "INSERT INTO users (name, email, password_hash, role, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, email, password_hash, role, created_at),
            )
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error):
                raise UniqueConstraintViolationError(str(error)) from error
            raise
        connection.commit()
        last_row_id = cursor.lastrowid
        if last_row_id is None:
            raise RuntimeError("Failed to obtain inserted user id")
        row = fetch_one_row(
            connection,
            "SELECT id, name, email, password_hash, role, created_at "
            "FROM users WHERE id = ?",
            (last_row_id,),
        )
    finally:
        connection.close()
    if row is None:
        raise RuntimeError("Inserted user row not found")
    return _row_to_user(row)
