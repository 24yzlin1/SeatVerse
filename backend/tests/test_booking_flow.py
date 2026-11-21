"""用例 2/3/5/6：活动座位隔离、重复提交、多座回滚、取消后重订。"""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from tests.helpers import auth_headers, book, login


def _scalar(
    database_path: Path, sql: str, parameters: tuple[object, ...] = ()
) -> object:
    connection = sqlite3.connect(database_path)
    try:
        row = connection.execute(sql, parameters).fetchone()
        assert row is not None
        return row[0]
    finally:
        connection.close()


def test_event_seat_isolation(client: TestClient, database_path: Path) -> None:
    token, _ = login(client, "user01@seatverse.local")
    created = book(client, token, 2, [1])
    assert created["code"] == 200, created

    assert (
        _scalar(
            database_path,
            "SELECT status FROM event_seats WHERE event_id = 2 AND seat_id = 1",
        )
        == "sold"
    )
    assert (
        _scalar(
            database_path,
            "SELECT status FROM event_seats WHERE event_id = 3 AND seat_id = 1",
        )
        == "available"
    )


def test_duplicate_submission(client: TestClient, database_path: Path) -> None:
    token, _ = login(client, "user01@seatverse.local")

    first = book(client, token, 2, [1])
    second = book(client, token, 2, [1])
    assert first["code"] == 200, first
    assert second["code"] == 409, second

    assert (
        _scalar(
            database_path,
            "SELECT COUNT(*) FROM booking_seats "
            "WHERE event_id = 2 AND seat_id = 1 AND is_active = 1",
        )
        == 1
    )
    assert _scalar(database_path, "SELECT COUNT(*) FROM tickets") == 1


def test_multi_seat_rollback(client: TestClient, database_path: Path) -> None:
    token1, _ = login(client, "user01@seatverse.local")
    token2, user2_id = login(client, "user02@seatverse.local")

    first = book(client, token1, 2, [1])
    assert first["code"] == 200, first

    failed = book(client, token2, 2, [2, 1])
    assert failed["code"] == 409, failed

    assert (
        _scalar(
            database_path,
            "SELECT status FROM event_seats WHERE event_id = 2 AND seat_id = 2",
        )
        == "available"
    )
    assert (
        _scalar(
            database_path,
            "SELECT COUNT(*) FROM bookings WHERE event_id = 2 AND user_id = ?",
            (user2_id,),
        )
        == 0
    )
    assert _scalar(database_path, "SELECT COUNT(*) FROM tickets") == 1


def test_cancel_and_rebook(client: TestClient, database_path: Path) -> None:
    token, _ = login(client, "user01@seatverse.local")

    created = book(client, token, 2, [1])
    assert created["code"] == 200, created
    payload = created["payload"]
    assert isinstance(payload, dict)
    booking_id = int(payload["id"])

    cancelled = client.post(
        f"/api/bookings/{booking_id}/cancel", headers=auth_headers(token)
    ).json()
    assert cancelled["code"] == 200, cancelled

    mine = client.get("/api/bookings/me", headers=auth_headers(token)).json()
    assert mine["code"] == 200, mine
    assert mine["payload"]["total"] == 1
    item = mine["payload"]["items"][0]
    assert item["status"] == "cancelled"
    assert item["cancelledAt"] is not None
    assert len(item["seats"]) == 1

    assert (
        _scalar(
            database_path,
            "SELECT status FROM event_seats WHERE event_id = 2 AND seat_id = 1",
        )
        == "available"
    )

    rebooked = book(client, token, 2, [1])
    assert rebooked["code"] == 200, rebooked

    mine_after = client.get(
        "/api/bookings/me", headers=auth_headers(token)
    ).json()
    assert mine_after["payload"]["total"] == 2
