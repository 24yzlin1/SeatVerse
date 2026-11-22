"""用例 1：空库从 migrate + seed 初始化后，数据量与 8 张表完整。"""

import sqlite3
from pathlib import Path

EXPECTED_TABLES = {
    "users",
    "venues",
    "seats",
    "events",
    "event_seats",
    "bookings",
    "booking_seats",
    "tickets",
}


def _count(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    assert row is not None
    return int(row[0])


def test_empty_database_initialization(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    try:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        assert tables == EXPECTED_TABLES

        assert _count(connection, "users") == 11
        assert _count(connection, "venues") == 1
        assert _count(connection, "seats") == 120
        assert _count(connection, "events") == 4
        assert _count(connection, "event_seats") == 360
        assert _count(connection, "bookings") == 0
        assert _count(connection, "booking_seats") == 0
        assert _count(connection, "tickets") == 0

        roles = dict(
            connection.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        )
        assert roles == {"organizer": 1, "user": 10}

        per_event = dict(
            connection.execute(
                "SELECT event_id, COUNT(*) FROM event_seats GROUP BY event_id"
            )
        )
        assert per_event == {1: 120, 2: 120, 3: 120}

        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()
