"""认证接口的回归用例（F 补，针对“刷新后主办方身份丢失”的缺陷）。

`auth.md §14.2` 规则 4：`GET /authentication/me` 的 `payload` 就是 user 对象本身，
不能再包一层 `{ "user": ... }`。前端 `bootstrap()` 直接用返回值覆盖 user 缓存，
多包一层会导致 `role` 读不到，刷新后主办方被当成普通用户。
"""

from typing import Any

from conftest import Harness, auth


def _body(response: Any) -> dict[str, Any]:
    value: object = response.json()
    assert isinstance(value, dict), f"响应不是对象: {value!r}"
    return value


def test_me_payload_is_user_object_not_wrapped(harness: Harness) -> None:
    response = harness.client.get(
        "/api/authentication/me", headers=auth(harness.token("organizer_one"))
    )
    body = _body(response)
    assert body["code"] == 200

    payload = body["payload"]
    assert isinstance(payload, dict)
    # 关键：payload 顶层直接是 id/name/email/role，不能再出现 user 包装层。
    assert set(payload) == {"id", "name", "email", "role"}
    assert payload["role"] == "organizer"
    assert payload["id"] == 1
    assert payload["name"] == "主办方甲"


def test_me_rejects_missing_or_invalid_token(harness: Harness) -> None:
    unauthorized = _body(harness.client.get("/api/authentication/me"))
    assert unauthorized["code"] == 401
    assert unauthorized["payload"] is None

    invalid = _body(
        harness.client.get(
            "/api/authentication/me",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
    )
    assert invalid["code"] == 401
