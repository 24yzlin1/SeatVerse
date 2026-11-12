"""预约相关的 HTTP 入口。

scope 只做参数校验、调用 core、包装统一响应；座位冲突、活动状态等业务判断都在 core。
"""

from fastapi import APIRouter, Depends

from app.core.bookings import create_booking as create_booking_core
from app.core.common import AppError
from app.scope.authentication import require_identity
from app.scope.common import ok
from app.types.authentication import Identity
from app.types.bookings import BookingPublic, CreateBookingRequest
from app.types.common import ResponsePayload

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("")
def create_booking(
    body: CreateBookingRequest,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[BookingPublic]:
    if body.eventId < 1:
        raise AppError(400, "活动编号必须为正整数")
    if not body.seatIds:
        raise AppError(400, "至少选择一个座位")
    if len(set(body.seatIds)) != len(body.seatIds):
        raise AppError(400, "座位编号不能重复")
    for seat_id in body.seatIds:
        if seat_id < 1:
            raise AppError(400, "座位编号必须为正整数")

    request = CreateBookingRequest(
        eventId=body.eventId,
        seatIds=list(body.seatIds),
    )
    return ok(create_booking_core(identity, request))
