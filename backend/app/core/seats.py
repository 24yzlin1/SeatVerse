"""Business use cases for per-event dynamic seat status.

Static coordinates are provided by `venues/{id}/seats`; this module only returns
`{seatId,status}` so the 3D page can color the matching seats by `seatId`.
"""

from app.core.common import AppError
from app.repos.events import find_event_by_id
from app.repos.seats import (
    list_event_seats as list_event_seats_repo,
    list_seats_by_venue,
)
from app.types.seats import (
    EventSeatListPayload,
    EventSeatStatePublic,
    SeatMapPayload,
    SeatPublic,
)
from datetime import datetime, timezone
from app.repos.seats import event_seat_statistics
from app.types.seats import SeatStatisticsPublic
from app.core.events import get_event_detail


def list_event_seats(event_id: int) -> EventSeatListPayload:
    event = find_event_by_id(event_id)
    if event is None:
        raise AppError(404, "Event not found")

    rows = list_event_seats_repo(event_id)
    items = [
        EventSeatStatePublic(seatId=row.seat_id, status=row.status) for row in rows
    ]
    return EventSeatListPayload(items=items)


def seat_map(event_id: int) -> SeatMapPayload:
    """Aggregate endpoint: returns event detail, static seats, and per-seat status
    in one response.

    The frontend seat-selection flow previously had to assemble three requests
    (`GET /events/{id}` → `GET /venues/{id}/seats` + `GET /events/{id}/seats`)
    and cross-validate them; here the server guarantees all three come from the
    same event/venue and are consistent by construction.
    """
    event = get_event_detail(event_id)

    seat_rows = list_seats_by_venue(event.venue.id)
    seats = [
        SeatPublic(
            id=row.id,
            row=row.row_number,
            number=row.seat_number,
            label=f"Row {row.row_number} Seat {row.seat_number}",
            seatType=row.seat_type,
            x=row.x,
            y=row.y,
            z=row.z,
        )
        for row in seat_rows
    ]

    state_rows = list_event_seats_repo(event_id)
    seat_states = [
        EventSeatStatePublic(seatId=row.seat_id, status=row.status)
        for row in state_rows
    ]
    return SeatMapPayload(event=event, seats=seats, seatStates=seat_states)


def seat_statistics(event_id: int) -> SeatStatisticsPublic:
    if find_event_by_id(event_id) is None:
        raise AppError(404, "Event not found")
    counts = event_seat_statistics(event_id)
    return SeatStatisticsPublic(
        eventId=event_id, total=counts.total, sold=counts.sold,
        locked=counts.locked, available=counts.available,
        updatedAt=datetime.now(timezone.utc).isoformat(),
    )
