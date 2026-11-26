"""用例 7：外键有效性与“有效占用”部分唯一索引。"""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.repos.database import get_connection
from tests.helpers import book, login


def test_foreign_key_and_active_unique_index(
    client: TestClient, database_path: Path
) -> None:
    token, _ = login(client, "user01@seatverse.local")
    created = book(client, token, 2, [1])
    assert created["code"] == 200, created
    payload = created["payload"]
    assert isinstance(payload, dict)
    first_booking_id = int(payload["id"])

    connection = get_connection()
    try:
        user2_row = connection.execute(
            "SELECT id FROM users WHERE email = ?", ("user02@seatverse.local",)
        ).fetchone()
        assert user2_row is not None
        user2_id = int(user2_row[0])

        cursor = connection.execute(
            "INSERT INTO bookings (event_id, user_id, status, created_at) "
            "VALUES (2, ?, 'reserved', '2026-11-21T00:00:00+00:00')",
            (user2_id,),
        )
        second_booking_id = cursor.lastrowid
        assert second_booking_id is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO event_seats (event_id, seat_id, status, version) "
                "VALUES (2, 99999, 'available', 0)"
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO booking_seats "
                "(booking_id, event_id, seat_id, is_active) "
                "VALUES (?, 2, 1, 1)",
                (second_booking_id,),
            )

        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM booking_seats "
                "WHERE event_id = 2 AND seat_id = 1 AND is_active = 1"
            ).fetchone()[0]
            == 1
        )
        assert first_booking_id > 0
    finally:
        connection.close()


def test_duplicate_seat_ids_rejected(client: TestClient) -> None:
    token, _ = login(client, "user01@seatverse.local")
    body = book(client, token, 2, [1, 1])
    assert body["code"] == 400, body
