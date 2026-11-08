import os
import sqlite3
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from pathlib import Path

from app.types.database import DatabaseConnection

_DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "var" / "seatverse.db"
_BUSY_TIMEOUT_MILLISECONDS = 15000


def get_database_path() -> Path:
    configured_path = os.environ.get("SEATVERSE_DATABASE_PATH")
    if configured_path:
        return Path(configured_path)
    return _DEFAULT_DATABASE_PATH


def get_connection() -> DatabaseConnection:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        database_path,
        timeout=_BUSY_TIMEOUT_MILLISECONDS / 1000,
    )
    connection.isolation_level = None
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MILLISECONDS}")
    return connection


def fetch_one_row(
    connection: DatabaseConnection,
    sql: str,
    parameters: Sequence[object] = (),
) -> sqlite3.Row | None:
    cursor = connection.execute(sql, parameters)
    raw_row: object = cursor.fetchone()
    if raw_row is None:
        return None
    if not isinstance(raw_row, sqlite3.Row):
        raise TypeError("Row factory is not configured to sqlite3.Row")
    return raw_row


def fetch_all_rows(
    connection: DatabaseConnection,
    sql: str,
    parameters: Sequence[object] = (),
) -> list[sqlite3.Row]:
    cursor = connection.execute(sql, parameters)
    raw_rows: list[object] = cursor.fetchall()
    result: list[sqlite3.Row] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, sqlite3.Row):
            raise TypeError("Row factory is not configured to sqlite3.Row")
        result.append(raw_row)
    return result


def read_text(row: sqlite3.Row, column: str) -> str:
    value: object = row[column]
    if not isinstance(value, str):
        raise TypeError(f"Column {column} is not text")
    return value


def read_integer(row: sqlite3.Row, column: str) -> int:
    value: object = row[column]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"Column {column} is not an integer")
    return value


def read_optional_text(row: sqlite3.Row, column: str) -> str | None:
    value: object = row[column]
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Column {column} is neither text nor null")
    return value


@contextmanager
def immediate_transaction(
    connection: DatabaseConnection,
) -> Generator[None, None, None]:
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    else:
        connection.execute("COMMIT")
