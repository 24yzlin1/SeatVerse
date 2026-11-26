"""Business use cases for venues and their fixed seats.

Seat coordinates come from the repos; this core module only:
- validates that the venue exists;
- converts database rows into `SeatPublic` for the frontend;
- builds the `label` (e.g. "Row 3 Seat 12").
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
        raise AppError(404, "Venue not found")

    rows = list_seats_by_venue(venue_id)
    items = [
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
        for row in rows
    ]
    return SeatListPayload(items=items)
