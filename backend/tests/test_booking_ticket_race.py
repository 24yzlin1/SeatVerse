"""P1：取消与核验的竞争和状态一致性（E/F 联合用例）。

覆盖三种情况：
1. 先核验成功 -> 再取消，必须 409；
2. 先取消成功 -> 再核验，必须 409；
3. 取消与核验同时发生 -> 恰好一方成功，数据库状态与胜者一致。
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from fastapi.testclient import TestClient

from app.core.bookings import cancel_booking
from app.core.common import AppError
from app.core.tickets import verify_ticket
from app.types.authentication import Identity
from tests.helpers import auth_headers, book, login


def _booking_payload(body: dict[str, object]) -> tuple[int, str]:
    payload = body["payload"]
    assert isinstance(payload, dict)
    return int(payload["id"]), str(payload["ticketCode"])


def test_cancel_after_verify_returns_409(
    client: TestClient, database_path: Path
) -> None:
    user_token, _ = login(client, "user01@seatverse.local")
    organizer_token, _ = login(
        client, "organizer@seatverse.local", "Organizer123!"
    )

    created = book(client, user_token, 2, [1])
    assert created["code"] == 200, created
    booking_id, ticket_code = _booking_payload(created)

    verified = client.post(
        "/api/tickets/verify",
        headers=auth_headers(organizer_token),
        json={"ticketCode": ticket_code},
    ).json()
    assert verified["code"] == 200, verified
    assert verified["payload"]["status"] == "used"

    cancelled = client.post(
        f"/api/bookings/{booking_id}/cancel", headers=auth_headers(user_token)
    ).json()
    assert cancelled["code"] == 409, cancelled

    mine = client.get("/api/bookings/me", headers=auth_headers(user_token)).json()
    assert mine["payload"]["items"][0]["status"] == "used"

    connection = sqlite3.connect(database_path)
    try:
        assert (
            connection.execute(
                "SELECT status FROM event_seats WHERE event_id = 2 AND seat_id = 1"
            ).fetchone()[0]
            == "sold"
        )
        assert (
            connection.execute(
                "SELECT verified_at FROM tickets WHERE ticket_code = ?",
                (ticket_code,),
            ).fetchone()[0]
            is not None
        )
    finally:
        connection.close()


def test_verify_after_cancel_returns_409(
    client: TestClient, database_path: Path
) -> None:
    user_token, _ = login(client, "user01@seatverse.local")
    organizer_token, _ = login(
        client, "organizer@seatverse.local", "Organizer123!"
    )

    created = book(client, user_token, 2, [1])
    assert created["code"] == 200, created
    booking_id, ticket_code = _booking_payload(created)

    cancelled = client.post(
        f"/api/bookings/{booking_id}/cancel", headers=auth_headers(user_token)
    ).json()
    assert cancelled["code"] == 200, cancelled

    verified = client.post(
        "/api/tickets/verify",
        headers=auth_headers(organizer_token),
        json={"ticketCode": ticket_code},
    ).json()
    assert verified["code"] == 409, verified

    mine = client.get("/api/bookings/me", headers=auth_headers(user_token)).json()
    assert mine["payload"]["items"][0]["status"] == "cancelled"

    ticket = client.get(
        f"/api/bookings/{booking_id}/ticket", headers=auth_headers(user_token)
    ).json()
    assert ticket["code"] == 200, ticket
    assert ticket["payload"]["status"] == "cancelled"

    connection = sqlite3.connect(database_path)
    try:
        assert (
            connection.execute(
                "SELECT status FROM event_seats WHERE event_id = 2 AND seat_id = 1"
            ).fetchone()[0]
            == "available"
        )
        assert (
            connection.execute(
                "SELECT verified_at FROM tickets WHERE ticket_code = ?",
                (ticket_code,),
            ).fetchone()[0]
            is None
        )
    finally:
        connection.close()


def test_concurrent_cancel_and_verify_only_one_wins(
    client: TestClient, database_path: Path
) -> None:
    user_token, user_id = login(client, "user01@seatverse.local")
    created = book(client, user_token, 2, [1])
    assert created["code"] == 200, created
    booking_id, ticket_code = _booking_payload(created)

    connection = sqlite3.connect(database_path)
    try:
        organizer_row = connection.execute(
            "SELECT id FROM users WHERE role = 'organizer' ORDER BY id LIMIT 1"
        ).fetchone()
        assert organizer_row is not None
        organizer_id = int(organizer_row[0])
    finally:
        connection.close()

    barrier = Barrier(2, timeout=30)

    def cancel_worker() -> int:
        barrier.wait()
        try:
            cancel_booking(
                Identity(user_id=user_id, role="user"),
                booking_id,
            )
        except AppError as error:
            return error.code
        return 200

    def verify_worker() -> int:
        barrier.wait()
        try:
            verify_ticket(
                Identity(user_id=organizer_id, role="organizer"),
                ticket_code,
            )
        except AppError as error:
            return error.code
        return 200

    with ThreadPoolExecutor(max_workers=2) as executor:
        cancel_future = executor.submit(cancel_worker)
        verify_future = executor.submit(verify_worker)
        codes = [cancel_future.result(), verify_future.result()]

    assert sorted(codes) == [200, 409], codes

    connection = sqlite3.connect(database_path)
    try:
        booking_status = connection.execute(
            "SELECT status FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()[0]
        seat_status = connection.execute(
            "SELECT status FROM event_seats WHERE event_id = 2 AND seat_id = 1"
        ).fetchone()[0]
        verified_at = connection.execute(
            "SELECT verified_at FROM tickets WHERE ticket_code = ?", (ticket_code,)
        ).fetchone()[0]
        active_count = connection.execute(
            "SELECT COUNT(*) FROM booking_seats "
            "WHERE booking_id = ? AND is_active = 1",
            (booking_id,),
        ).fetchone()[0]
    finally:
        connection.close()

    if booking_status == "cancelled":
        assert seat_status == "available"
        assert verified_at is None
        assert active_count == 0
    elif booking_status == "used":
        assert seat_status == "sold"
        assert verified_at is not None
        assert active_count == 1
    else:
        raise AssertionError(f"unexpected booking status: {booking_status}")
