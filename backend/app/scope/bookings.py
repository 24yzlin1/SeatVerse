"""HTTP entry points for bookings.

The scope layer only validates parameters, calls core, and wraps the unified response; business checks such as seat conflicts and event status all live in core.
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
    event_id: int | None = Query(None, alias="eventId"),
    status: str | None = None,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[BookingPage]:
    if page < 1 or page_size < 1 or page_size > 100:
        raise AppError(400, "Page must be at least 1; page size must be between 1 and 100")
    return ok(list_my_bookings(identity, page, page_size, event_id, status))


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, identity: Identity = Depends(require_identity)
) -> ResponsePayload[CancelBookingPayload]:
    if booking_id < 1:
        raise AppError(400, "Booking id must be a positive integer")
    return ok(cancel_booking_core(identity, booking_id))


@router.post("")
def create_booking(
    body: CreateBookingRequest,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[BookingPublic]:
    if body.eventId < 1:
        raise AppError(400, "Event id must be a positive integer")
    if not body.seatIds:
        raise AppError(400, "At least one seat must be selected")
    if len(set(body.seatIds)) != len(body.seatIds):
        raise AppError(400, "Seat ids must not be duplicated")
    for seat_id in body.seatIds:
        if seat_id < 1:
            raise AppError(400, "Seat id must be a positive integer")

    request = CreateBookingRequest(
        eventId=body.eventId,
        seatIds=list(body.seatIds),
    )
    return ok(create_booking_core(identity, request))
