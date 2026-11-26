"""用例 4：10 个独立用户同时抢同一座位，1 成 9 败。

这里直接并发调用 core 的 `create_booking`，每个线程独立开 SQLite 连接，
验证的是 `BEGIN IMMEDIATE` + 条件更新 + 唯一索引这套事务机制。
真实 HTTP 层的 10 用户并发由 `scripts/concurrency_test.py` 覆盖。
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from app.core.bookings import create_booking
from app.core.common import AppError
from app.types.authentication import Identity
from app.types.bookings import CreateBookingRequest


def test_ten_users_race_for_same_seat(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    try:
        user_ids = [
            int(row[0])
            for row in connection.execute(
                "SELECT id FROM users WHERE role = 'user' ORDER BY id LIMIT 10"
            )
        ]
    finally:
        connection.close()
    assert len(user_ids) == 10

    barrier = Barrier(10)

    def attempt(user_id: int) -> int:
        barrier.wait()
        try:
            create_booking(
                Identity(user_id=user_id, role="user"),
                CreateBookingRequest(eventId=2, seatIds=[1]),
            )
        except AppError as error:
            return error.code
        return 200

    with ThreadPoolExecutor(max_workers=10) as executor:
        codes = list(executor.map(attempt, user_ids))

    assert sorted(codes) == [200] + [409] * 9

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
                "SELECT COUNT(*) FROM booking_seats "
                "WHERE event_id = 2 AND seat_id = 1 AND is_active = 1"
            ).fetchone()[0]
            == 1
        )
        assert connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 1
    finally:
        connection.close()
