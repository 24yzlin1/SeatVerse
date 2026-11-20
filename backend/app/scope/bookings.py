"""预约相关的 HTTP 入口。

scope 只做参数校验、调用 core、包装统一响应；座位冲突、活动状态等业务判断都在 core。
"""

from fastapi import APIRouter, Depends, Query

from app.core.bookings import create_booking as create_booking_core
from app.core.bookings import list_my_bookings, cancel_booking as cancel_booking_core
from app.core.common import AppError
from app.scope.authentication import require_identity
from app.scope.common import ok
from app.types.authentication import Identity
from app.types.bookings import (
    BookingPublic,
    CreateBookingRequest,
    BookingPage,
    CancelBookingPayload,
)
from app.types.common import ResponsePayload

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/me")
def my_bookings(
    page: int = 1,
    page_size: int = Query(20, alias="pageSize"),
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[BookingPage]:
    if page < 1 or page_size < 1 or page_size > 100:
        raise AppError(400, "页码必须大于等于 1，每页条数必须在 1 到 100 之间")
    return ok(list_my_bookings(identity, page, page_size))


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, identity: Identity = Depends(require_identity)
) -> ResponsePayload[CancelBookingPayload]:
    if booking_id < 1:
        raise AppError(400, "预约编号必须为正整数")
    return ok(cancel_booking_core(identity, booking_id))


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
