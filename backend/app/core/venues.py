"""场馆与场馆固定座位的业务用例。

座位坐标来自 repos，core 只负责：
- 校验场馆是否存在；
- 把数据库行转成前端需要的 `SeatPublic`；
- 拼出 `label`（如 3排12号）。
"""

from app.core.common import AppError
from app.repos.seats import list_seats_by_venue
from app.repos.venues import find_venue_by_id, list_venues as list_venues_repo
from app.types.seats import SeatListPayload, SeatPublic
from app.types.venues import VenuePage, VenuePublic


def list_venues(page: int, page_size: int) -> VenuePage:
    rows = list_venues_repo()
    total = len(rows)
    start = (page - 1) * page_size
    items = [
        VenuePublic(id=row.id, name=row.name, capacity=row.capacity)
        for row in rows[start : start + page_size]
    ]
    return VenuePage(items=items, total=total, page=page, pageSize=page_size)


def list_venue_seats(venue_id: int) -> SeatListPayload:
    venue = find_venue_by_id(venue_id)
    if venue is None:
        raise AppError(404, "场馆不存在")

    rows = list_seats_by_venue(venue_id)
    items = [
        SeatPublic(
            id=row.id,
            row=row.row_number,
            number=row.seat_number,
            label=f"{row.row_number}排{row.seat_number}号",
            seatType=row.seat_type,
            x=row.x,
            y=row.y,
            z=row.z,
        )
        for row in rows
    ]
    return SeatListPayload(items=items)
