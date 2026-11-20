"""票务与主办方接口测试夹具（F 负责）。

每次测试建一个临时 SQLite 库，执行真实迁移 SQL（`app/repos/migrations/000_schema.sql`），
再写入固定种子数据；接口通过 `TestClient` 走真实路由与真 JWT，不触碰开发库。

种子数据（编号固定，便于断言）：

| 活动 | 主办方 | 状态 | 时间 |
|---|---|---|---|
| 100 | 1 | published | 1 小时后开始，3 小时后结束 |
| 101 | 2 | published | 同上 |
| 102 | 1 | cancelled | 同上 |
| 103 | 1 | published | 3 小时前开始，1 小时前结束（已结束） |

| 预约 | 活动 | 用户 | 状态 | 票号 | 座位 |
|---|---|---|---|---|---|
| 9001 | 100 | 3 | reserved | SV7F3K9Q2M4T8X6B5N2P | 11、12 |
| 9002 | 100 | 4 | reserved | ABCDEFGHJKMNPQRSTVWX | 13 |
| 9003 | 100 | 3 | cancelled | 0123456789ABCDEFGHJK | 14（已释放） |
| 9004 | 101 | 3 | reserved | ZYXWVTSRQPNMKJHGFEDC | 11（另一活动，独立） |
| 9005 | 102 | 4 | reserved | K9Q2M4T8X6B5N2P7F3KD | 12 |
| 9006 | 103 | 4 | reserved | PQRSTVWXYZ0123456789 | 13 |
"""

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.security import issue_token
from main import app

SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "app" / "repos" / "migrations" / "000_schema.sql"
)
JWT_SECRET = "seatverse-test-secret-0123456789abcdef"

ORGANIZER_ONE_ID = 1
ORGANIZER_TWO_ID = 2
USER_ONE_ID = 3
USER_TWO_ID = 4

TICKET_CODE_BOOKING_9001 = "SV7F3K9Q2M4T8X6B5N2P"
TICKET_CODE_BOOKING_9002 = "ABCDEFGHJKMNPQRSTVWX"
TICKET_CODE_BOOKING_9003 = "0123456789ABCDEFGHJK"
TICKET_CODE_BOOKING_9004 = "ZYXWVTSRQPNMKJHGFEDC"
TICKET_CODE_BOOKING_9005 = "K9Q2M4T8X6B5N2P7F3KD"
TICKET_CODE_BOOKING_9006 = "PQRSTVWXYZ0123456789"


@dataclass(frozen=True)
class Harness:
    client: TestClient
    database_path: Path
    tokens: dict[str, str]

    def token(self, role: str) -> str:
        return self.tokens[role]


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def _seed(connection: sqlite3.Connection) -> None:
    now = datetime.now(timezone.utc)
    past_start = now - timedelta(hours=3)
    past_end = now - timedelta(hours=1)
    future_start = now + timedelta(hours=1)
    future_end = now + timedelta(hours=3)
    created_at = _iso(now)

    connection.executemany(
        "INSERT INTO users (id, name, email, password_hash, role, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                ORGANIZER_ONE_ID,
                "主办方甲",
                "organizer-one@example.com",
                "unused",
                "organizer",
                created_at,
            ),
            (
                ORGANIZER_TWO_ID,
                "主办方乙",
                "organizer-two@example.com",
                "unused",
                "organizer",
                created_at,
            ),
            (USER_ONE_ID, "用户甲", "user-one@example.com", "unused", "user", created_at),
            (USER_TWO_ID, "用户乙", "user-two@example.com", "unused", "user", created_at),
        ],
    )
    connection.execute(
        "INSERT INTO venues (id, name, layout_config, capacity) VALUES (1, ?, '{}', 4)",
        ("大学生活动中心",),
    )
    connection.executemany(
        "INSERT INTO seats (id, venue_id, row_number, seat_number, x, y, z, seat_type) "
        "VALUES (?, 1, 1, ?, ?, 0, 0, 'standard')",
        [
            (11, 1, 0.0),
            (12, 2, 1.0),
            (13, 3, 2.0),
            (14, 4, 3.0),
        ],
    )
    connection.executemany(
        "INSERT INTO events (id, title, description, start_time, end_time, "
        "organizer_id, venue_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
        [
            (100, "周五讲座", "正常活动", _iso(future_start), _iso(future_end), ORGANIZER_ONE_ID, "published", created_at),
            (101, "别人的活动", "另一主办方", _iso(future_start), _iso(future_end), ORGANIZER_TWO_ID, "published", created_at),
            (102, "取消的活动", "活动已取消", _iso(future_start), _iso(future_end), ORGANIZER_ONE_ID, "cancelled", created_at),
            (103, "已结束的活动", "活动已结束", _iso(past_start), _iso(past_end), ORGANIZER_ONE_ID, "published", created_at),
        ],
    )
    connection.executemany(
        "INSERT INTO bookings (id, event_id, user_id, status, created_at, cancelled_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (9001, 100, USER_ONE_ID, "reserved", created_at, None),
            (9002, 100, USER_TWO_ID, "reserved", created_at, None),
            (9003, 100, USER_ONE_ID, "cancelled", created_at, created_at),
            (9004, 101, USER_ONE_ID, "reserved", created_at, None),
            (9005, 102, USER_TWO_ID, "reserved", created_at, None),
            (9006, 103, USER_TWO_ID, "reserved", created_at, None),
        ],
    )
    connection.executemany(
        "INSERT INTO booking_seats (booking_id, event_id, seat_id, is_active) "
        "VALUES (?, ?, ?, ?)",
        [
            (9001, 100, 11, 1),
            (9001, 100, 12, 1),
            (9002, 100, 13, 1),
            (9003, 100, 14, 0),
            (9004, 101, 11, 1),
            (9005, 102, 12, 1),
            (9006, 103, 13, 1),
        ],
    )
    connection.executemany(
        "INSERT INTO tickets (id, booking_id, ticket_code) VALUES (?, ?, ?)",
        [
            (5001, 9001, TICKET_CODE_BOOKING_9001),
            (5002, 9002, TICKET_CODE_BOOKING_9002),
            (5003, 9003, TICKET_CODE_BOOKING_9003),
            (5004, 9004, TICKET_CODE_BOOKING_9004),
            (5005, 9005, TICKET_CODE_BOOKING_9005),
            (5006, 9006, TICKET_CODE_BOOKING_9006),
        ],
    )


@pytest.fixture()
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Harness]:
    database_path = tmp_path / "seatverse-test.db"
    monkeypatch.setenv("SEATVERSE_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("SEATVERSE_JWT_SECRET", JWT_SECRET)

    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _seed(connection)
        connection.commit()
    finally:
        connection.close()

    tokens = {
        "organizer_one": issue_token(ORGANIZER_ONE_ID, "organizer"),
        "organizer_two": issue_token(ORGANIZER_TWO_ID, "organizer"),
        "user_one": issue_token(USER_ONE_ID, "user"),
        "user_two": issue_token(USER_TWO_ID, "user"),
    }

    # Starlette 在统一异常处理器发出响应后仍会把异常抛给服务器，
    # 测试必须关掉重新抛出，才能拿到已经写好的 {code,message,payload} 信封。
    with TestClient(app, raise_server_exceptions=False) as client:
        yield Harness(client=client, database_path=database_path, tokens=tokens)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
