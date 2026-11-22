"""Type definitions for seats and per-event seat states.

Corresponding tables: `seats`, `event_seats` (see backend/app/repos/migrations/000_schema.sql).
Corresponding enums: docs/contracts/enums.md §2.3 (EventSeatStatus), §2.6 (SeatType).

Conventions:
- `*Row` is a data row exposed by the repos layer; fields map one-to-one to table columns;
- `*Public` / `*Payload` are response models returned by the scope layer to the frontend; JSON keys use camelCase per the contract.
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from app.types.events import EventPublic

SeatType = Literal["standard"]
EventSeatStatus = Literal["available", "locked", "sold"]


@dataclass(frozen=True)
class SeatRow:
    """A row of the `seats` table: fixed seat coordinates shared by all events."""

    id: int
    venue_id: int
    row_number: int
    seat_number: int
    x: float
    y: float
    z: float
    seat_type: SeatType


@dataclass(frozen=True)
class EventSeatRow:
    """A row of the `event_seats` table: dynamic state of a seat within a specific event."""

    id: int
    event_id: int
    seat_id: int
    status: EventSeatStatus
    version: int


@dataclass(frozen=True)
class EventSeatStateRow:
    """Query result of `GET /events/{id}/seats`: dynamic states only; coordinates are provided by the static endpoint."""

    seat_id: int
    status: EventSeatStatus


class SeatPublic(BaseModel):
    """Static seat response; fields align with the frontend `StaticSeat`."""

    id: int
    row: int
    number: int
    label: str
    seatType: SeatType
    x: float
    y: float
    z: float


class SeatListPayload(BaseModel):
    items: list[SeatPublic]


class EventSeatStatePublic(BaseModel):
    """Dynamic seat response; fields align with the frontend `EventSeatState`."""

    seatId: int
    status: EventSeatStatus


class EventSeatListPayload(BaseModel):
    items: list[EventSeatStatePublic]


class SeatMapPayload(BaseModel):
    """Aggregated response of `GET /events/{id}/seat-map`: event + static seats + dynamic states.

    Equivalent to a joined view of the three endpoints (event detail, venue seats, event seats),
    so the frontend no longer needs to assemble three requests and cross-check associations.
    """

    event: EventPublic
    seats: list[SeatPublic]
    seatStates: list[EventSeatStatePublic]


@dataclass(frozen=True)
class SeatStatisticsRow:
    total: int
    sold: int
    locked: int
    available: int


class SeatStatisticsPublic(BaseModel):
    eventId: int
    total: int
    sold: int
    locked: int
    available: int
    updatedAt: str
