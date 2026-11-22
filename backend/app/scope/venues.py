"""HTTP entry points for venues.

The scope layer only validates parameters, calls core, and wraps the unified response; it writes no SQL and assembles no business fields.
"""

from fastapi import APIRouter, Query

from app.core.common import AppError
from app.core.venues import list_venue_seats as list_venue_seats_core
from app.core.venues import list_venues as list_venues_core
from app.scope.common import ok
from app.types.common import ResponsePayload
from app.types.seats import SeatListPayload
from app.types.venues import VenuePage

router = APIRouter(prefix="/venues", tags=["venues"])
_MAXIMUM_PAGE_SIZE = 100


@router.get("")
def list_venues(
    page: int = 1,
    page_size: int = Query(20, alias="pageSize"),
) -> ResponsePayload[VenuePage]:
    if page < 1:
        raise AppError(400, "Page must be at least 1")
    if page_size < 1 or page_size > _MAXIMUM_PAGE_SIZE:
        raise AppError(400, f"Page size must be between 1 and {_MAXIMUM_PAGE_SIZE}")
    return ok(list_venues_core(page, page_size))


@router.get("/{venue_id}/seats")
def list_venue_seats(venue_id: int) -> ResponsePayload[SeatListPayload]:
    if venue_id < 1:
        raise AppError(400, "Venue id must be a positive integer")
    return ok(list_venue_seats_core(venue_id))
