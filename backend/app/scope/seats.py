"""HTTP entry points for per-event dynamic seats.

The path is `/events/{id}/seats`, parallel to D's `/events` and `/events/{id}`;
when mounted, the `/api` router in main.py adds the prefix uniformly.
"""

from fastapi import APIRouter

from app.core.common import AppError
from app.core.seats import (
    list_event_seats as list_event_seats_core,
    seat_map as seat_map_core,
)
from app.scope.common import ok
from app.types.common import ResponsePayload
from app.types.seats import EventSeatListPayload, SeatMapPayload
from app.types.seats import SeatStatisticsPublic
from app.core.seats import seat_statistics as seat_statistics_core

router = APIRouter(prefix="/events", tags=["seats"])


@router.get("/{event_id}/seat-map")
def seat_map(event_id: int) -> ResponsePayload[SeatMapPayload]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    return ok(seat_map_core(event_id))


@router.get("/{event_id}/seat-statistics")
def seat_statistics(event_id: int) -> ResponsePayload[SeatStatisticsPublic]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    return ok(seat_statistics_core(event_id))


@router.get("/{event_id}/seats")
def list_event_seats(event_id: int) -> ResponsePayload[EventSeatListPayload]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    return ok(list_event_seats_core(event_id))
