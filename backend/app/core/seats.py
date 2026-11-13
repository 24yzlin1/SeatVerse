"""每场活动动态座位状态的业务用例。

静态坐标由 `venues/{id}/seats` 提供；这里只返回 `{seatId,status}`，
让 3D 页面按 `seatId` 把颜色贴到对应座位上。
"""

from app.core.common import AppError
from app.repos.events import find_event_by_id
from app.repos.seats import list_event_seats as list_event_seats_repo
from app.types.seats import EventSeatListPayload, EventSeatStatePublic


def list_event_seats(event_id: int) -> EventSeatListPayload:
    event = find_event_by_id(event_id)
    if event is None:
        raise AppError(404, "活动不存在")

    rows = list_event_seats_repo(event_id)
    items = [
        EventSeatStatePublic(seatId=row.seat_id, status=row.status) for row in rows
    ]
    return EventSeatListPayload(items=items)
