"""测试用的小工具：登录、带 token 的请求头、提交预约。"""

from fastapi.testclient import TestClient


def login(
    client: TestClient, email: str, password: str = "User12345!"
) -> tuple[str, int]:
    body = client.post(
        "/api/authentication/login",
        json={"email": email, "password": password},
    ).json()
    assert body["code"] == 200, body
    return str(body["payload"]["token"]), int(body["payload"]["user"]["id"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def book(
    client: TestClient, token: str, event_id: int, seat_ids: list[int]
) -> dict[str, object]:
    body: dict[str, object] = client.post(
        "/api/bookings",
        headers=auth_headers(token),
        json={"eventId": event_id, "seatIds": seat_ids},
    ).json()
    return body
