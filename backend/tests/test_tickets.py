"""票务与主办方接口用例（F 负责，对应 05 号分工表 F 的验收项）。

覆盖：
1. 本人票可查、他人票与不存在同码同文案（防枚举）；
2. 有效票核验成功、重复核验 409 且回显首次核验时间；
3. 已取消预约 / 已取消活动 / 已结束活动不能签到；
4. 角色不足 403、跨主办方 404，名单只给本活动主办方；
5. 名单分页参数校验，以及主办方创建活动、`pageSize` 参数生效。
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from conftest import (
    TICKET_CODE_BOOKING_9001,
    TICKET_CODE_BOOKING_9002,
    TICKET_CODE_BOOKING_9003,
    TICKET_CODE_BOOKING_9005,
    TICKET_CODE_BOOKING_9006,
    Harness,
    auth,
)

_TICKET_NOT_FOUND_MESSAGE = "票号不存在或无权查看"
_EVENT_NOT_FOUND_MESSAGE = "活动不存在或无权查看"


def _body(response: Any) -> dict[str, Any]:
    value: object = response.json()
    assert isinstance(value, dict), f"响应不是对象: {value!r}"
    return value


def _payload(response: Any) -> dict[str, Any]:
    body = _body(response)
    assert body["code"] == 200, f"期望成功信封，实际: {body!r}"
    payload = body["payload"]
    assert isinstance(payload, dict), f"payload 不是对象: {payload!r}"
    return payload


def _expect_error(response: Any, code: int, message: str | None = None) -> None:
    body = _body(response)
    assert body["code"] == code, f"期望 code={code}，实际: {body!r}"
    assert body["payload"] is None
    if message is not None:
        assert body["message"] == message


def _fetch_booking_status(harness: Harness, booking_id: int) -> str:
    connection = sqlite3.connect(harness.database_path)
    try:
        row = connection.execute(
            "SELECT status FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()
    finally:
        connection.close()
    assert row is not None, f"预约 {booking_id} 不存在"
    status: object = row[0]
    assert isinstance(status, str)
    return status


def _fetch_verified_at(harness: Harness, ticket_code: str) -> str | None:
    connection = sqlite3.connect(harness.database_path)
    try:
        row = connection.execute(
            "SELECT verified_at FROM tickets WHERE ticket_code = ?", (ticket_code,)
        ).fetchone()
    finally:
        connection.close()
    assert row is not None, f"票 {ticket_code} 不存在"
    verified_at: object = row[0]
    assert verified_at is None or isinstance(verified_at, str)
    return verified_at


def test_ticket_by_booking_id_returns_contract_shape(harness: Harness) -> None:
    client = harness.client
    payload = _payload(
        client.get("/api/bookings/9001/ticket", headers=auth(harness.token("user_one")))
    )
    assert payload["bookingId"] == 9001
    assert payload["ticketCode"] == TICKET_CODE_BOOKING_9001
    assert payload["status"] == "reserved"
    assert payload["verifiedAt"] is None

    event = payload["event"]
    assert isinstance(event, dict)
    assert event["id"] == 100
    assert isinstance(event["startTime"], str)
    venue = event["venue"]
    assert isinstance(venue, dict)
    assert venue["name"] == "大学生活动中心"

    seats = payload["seats"]
    assert isinstance(seats, list)
    labels = [seat["label"] for seat in seats if isinstance(seat, dict)]
    assert labels == ["1排1号", "1排2号"]

    # 已取消的预约仍能查票，票面派生为“已失效”。
    cancelled = _payload(
        client.get("/api/bookings/9003/ticket", headers=auth(harness.token("user_one")))
    )
    assert cancelled["status"] == "cancelled"


def test_ticket_by_booking_id_hides_other_users_and_missing(harness: Harness) -> None:
    client = harness.client
    _expect_error(
        client.get("/api/bookings/9001/ticket", headers=auth(harness.token("user_two"))),
        404,
        _TICKET_NOT_FOUND_MESSAGE,
    )
    _expect_error(
        client.get("/api/bookings/999999/ticket", headers=auth(harness.token("user_one"))),
        404,
        _TICKET_NOT_FOUND_MESSAGE,
    )
    _expect_error(client.get("/api/bookings/9001/ticket"), 401)


def test_ticket_by_code_normalizes_input(harness: Harness) -> None:
    client = harness.client
    headers = auth(harness.token("user_one"))

    lowercase = _payload(
        client.get(f"/api/tickets/{TICKET_CODE_BOOKING_9001.lower()}", headers=headers)
    )
    assert lowercase["ticketCode"] == TICKET_CODE_BOOKING_9001

    with_hyphen = _payload(
        client.get(
            f"/api/tickets/{TICKET_CODE_BOOKING_9001[:4]}-{TICKET_CODE_BOOKING_9001[4:]}",
            headers=headers,
        )
    )
    assert with_hyphen["ticketCode"] == TICKET_CODE_BOOKING_9001

    # 他人票与格式非法统一 404，避免枚举探测。
    _expect_error(
        client.get(f"/api/tickets/{TICKET_CODE_BOOKING_9002}", headers=headers),
        404,
        _TICKET_NOT_FOUND_MESSAGE,
    )
    _expect_error(
        client.get("/api/tickets/NOT-A-TICKET", headers=headers),
        404,
        _TICKET_NOT_FOUND_MESSAGE,
    )


def test_verify_marks_ticket_used_and_rejects_duplicate(harness: Harness) -> None:
    client = harness.client
    headers = auth(harness.token("organizer_one"))

    first = _payload(
        client.post(
            "/api/tickets/verify",
            json={"ticketCode": TICKET_CODE_BOOKING_9001},
            headers=headers,
        )
    )
    assert first["status"] == "used"
    verified_at = first["verifiedAt"]
    assert isinstance(verified_at, str)
    assert first["verifiedBy"] == 1
    assert _fetch_booking_status(harness, 9001) == "used"
    assert _fetch_verified_at(harness, TICKET_CODE_BOOKING_9001) == verified_at

    second = client.post(
        "/api/tickets/verify",
        json={"ticketCode": TICKET_CODE_BOOKING_9001.lower()},
        headers=headers,
    )
    _expect_error(second, 409)
    message = _body(second)["message"]
    assert isinstance(message, str)
    expected_display = (
        datetime.fromisoformat(verified_at)
        .astimezone(timezone(timedelta(hours=8)))
        .strftime("%Y-%m-%d %H:%M:%S")
    )
    assert expected_display in message, "重复核验的 409 必须回显格式化后的首次核验时间"
    assert "T" not in message, "message 里不应再出现 ISO 8601 原始时间"

    # 再查票，状态保持 used（条件更新不会把已核验票改回 reserved）。
    refreshed = _payload(
        client.get(
            f"/api/tickets/{TICKET_CODE_BOOKING_9001}",
            headers=auth(harness.token("user_one")),
        )
    )
    assert refreshed["status"] == "used"
    assert refreshed["verifiedAt"] == verified_at


def test_verify_rejects_wrong_role_and_other_organizer(harness: Harness) -> None:
    client = harness.client

    _expect_error(
        client.post(
            "/api/tickets/verify",
            json={"ticketCode": TICKET_CODE_BOOKING_9001},
            headers=auth(harness.token("user_one")),
        ),
        403,
    )
    _expect_error(
        client.post(
            "/api/tickets/verify",
            json={"ticketCode": TICKET_CODE_BOOKING_9001},
            headers=auth(harness.token("organizer_two")),
        ),
        404,
        _TICKET_NOT_FOUND_MESSAGE,
    )
    _expect_error(
        client.post(
            "/api/tickets/verify",
            json={"ticketCode": TICKET_CODE_BOOKING_9001},
        ),
        401,
    )


def test_verify_rejects_cancelled_booking(harness: Harness) -> None:
    response = harness.client.post(
        "/api/tickets/verify",
        json={"ticketCode": TICKET_CODE_BOOKING_9003},
        headers=auth(harness.token("organizer_one")),
    )
    _expect_error(response, 409)
    message = _body(response)["message"]
    assert isinstance(message, str)
    assert "取消" in message


def test_verify_rejects_cancelled_and_ended_events(harness: Harness) -> None:
    client = harness.client
    headers = auth(harness.token("organizer_one"))

    cancelled_event = client.post(
        "/api/tickets/verify",
        json={"ticketCode": TICKET_CODE_BOOKING_9005},
        headers=headers,
    )
    _expect_error(cancelled_event, 409)
    cancelled_message = _body(cancelled_event)["message"]
    assert isinstance(cancelled_message, str)
    assert "取消" in cancelled_message

    ended_event = client.post(
        "/api/tickets/verify",
        json={"ticketCode": TICKET_CODE_BOOKING_9006},
        headers=headers,
    )
    _expect_error(ended_event, 409)
    ended_message = _body(ended_event)["message"]
    assert isinstance(ended_message, str)
    assert "结束" in ended_message


def test_roster_lists_only_own_event(harness: Harness) -> None:
    client = harness.client
    headers = auth(harness.token("organizer_one"))

    page = _payload(client.get("/api/events/100/bookings", headers=headers))
    assert page["total"] == 3
    assert page["page"] == 1
    assert page["pageSize"] == 20

    items = page["items"]
    assert isinstance(items, list)
    assert [item["id"] for item in items if isinstance(item, dict)] == [9001, 9002, 9003]

    first = items[0]
    assert isinstance(first, dict)
    assert first["ticketCode"] == TICKET_CODE_BOOKING_9001
    assert first["verifiedAt"] is None
    user = first["user"]
    assert isinstance(user, dict)
    assert user["name"] == "用户甲"

    cancelled = items[2]
    assert isinstance(cancelled, dict)
    assert cancelled["status"] == "cancelled"
    seats = cancelled["seats"]
    assert isinstance(seats, list)
    assert len(seats) == 1

    # 他人活动 404、普通用户 403、未登录 401。
    _expect_error(
        client.get(
            "/api/events/100/bookings", headers=auth(harness.token("organizer_two"))
        ),
        404,
        _EVENT_NOT_FOUND_MESSAGE,
    )
    _expect_error(
        client.get("/api/events/100/bookings", headers=auth(harness.token("user_one"))),
        403,
    )
    _expect_error(client.get("/api/events/100/bookings"), 401)


def test_roster_pagination(harness: Harness) -> None:
    client = harness.client
    headers = auth(harness.token("organizer_one"))

    second_page = _payload(
        client.get("/api/events/100/bookings?page=2&pageSize=2", headers=headers)
    )
    assert second_page["total"] == 3
    assert second_page["pageSize"] == 2
    items = second_page["items"]
    assert isinstance(items, list)
    assert [item["id"] for item in items if isinstance(item, dict)] == [9003]

    _expect_error(client.get("/api/events/100/bookings?page=0", headers=headers), 400)
    _expect_error(client.get("/api/events/100/bookings?pageSize=0", headers=headers), 400)
    _expect_error(client.get("/api/events/100/bookings?pageSize=101", headers=headers), 400)


def test_create_event_requires_organizer_and_returns_owner(harness: Harness) -> None:
    client = harness.client
    payload = {
        "title": "新建讲座",
        "description": "主办方自建",
        "startTime": "2026-12-20T19:00:00+08:00",
        "endTime": "2026-12-20T21:00:00+08:00",
    }

    created = _payload(
        client.post(
            "/api/events",
            json=payload,
            headers=auth(harness.token("organizer_one")),
        )
    )
    assert created["title"] == "新建讲座"
    assert created["status"] == "draft"
    assert created["organizerId"] == 1
    assert isinstance(created["startTime"], str)

    _expect_error(
        client.post("/api/events", json=payload, headers=auth(harness.token("user_one"))),
        403,
    )
    _expect_error(
        client.post(
            "/api/events",
            json={**payload, "title": "   "},
            headers=auth(harness.token("organizer_one")),
        ),
        400,
    )
    _expect_error(
        client.post(
            "/api/events",
            json={
                **payload,
                "startTime": "2026-12-20T21:00:00+08:00",
                "endTime": "2026-12-20T19:00:00+08:00",
            },
            headers=auth(harness.token("organizer_one")),
        ),
        400,
    )


def test_event_list_honors_page_size(harness: Harness) -> None:
    response = harness.client.get("/api/events?page=1&pageSize=2")
    body = _body(response)
    assert body["code"] == 200
    payload = body["payload"]
    assert isinstance(payload, dict)
    assert payload["total"] >= 4
    items = payload["items"]
    assert isinstance(items, list)
    assert len(items) == 2
    assert payload["pageSize"] == 2
