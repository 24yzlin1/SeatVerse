"""每场活动动态座位的 HTTP 入口。

路径是 `/events/{id}/seats`，与 D 的 `/events`、`/events/{id}` 并列；
挂载时统一由 main.py 的 `/api` router 加前缀。
"""

from fastapi import APIRouter

from app.core.common import AppError
from app.core.seats import list_event_seats as list_event_seats_core
from app.scope.common import ok
from app.types.common import ResponsePayload
from app.types.seats import EventSeatListPayload

router = APIRouter(prefix="/events", tags=["seats"])


@router.get("/{event_id}/seats")
def list_event_seats(event_id: int) -> ResponsePayload[EventSeatListPayload]:
    if event_id < 1:
        raise AppError(400, "活动编号必须为正整数")
    return ok(list_event_seats_core(event_id))
