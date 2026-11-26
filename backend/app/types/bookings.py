"""Type definitions for bookings, booking seats, and "My Bookings".

Corresponding tables: `bookings`, `booking_seats` (see backend/app/repos/migrations/000_schema.sql).
Corresponding contracts: docs/contracts/api.md §4.1 / §4.2, docs/contracts/enums.md §2.2 / §2.4.

Conventions:
- `*Row` is a data row exposed by the repos layer; fields map one-to-one to query columns;
- `*Public` / `*Payload` are response models; JSON keys use camelCase to match the pinned samples;
- Time fields are always ISO 8601 strings with timezone offsets; no parsing happens at the types layer.
"""

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.types.seats import SeatType

EventStatus = Literal["draft", "published", "closed", "cancelled"]
BookingStatus = Literal["reserved", "cancelled", "used"]


@dataclass(frozen=True)
class BookingRow:
    """A row of the `bookings` table."""

    id: int
    event_id: int
    user_id: int
    status: BookingStatus
    created_at: str
    cancelled_at: str | None


@dataclass(frozen=True)
class BookingSeatRow:
    """A row of the `booking_seats` table.

    `is_active` is stored as INTEGER 0/1 in the database; the repos row mapping converts it to bool explicitly;
    only records with `is_active = 1` participate in seat holding and the uniqueness constraint.
    """

    id: int
    booking_id: int
    event_id: int
    seat_id: int
    is_active: bool


@dataclass(frozen=True)
class BookingEventRow:
    """Event info read within the booking transaction (same connection, bypassing D's events repo)."""

    event_id: int
    status: EventStatus
    start_time: str
    end_time: str
    venue_id: int


@dataclass(frozen=True)
class BookingListRow:
    """JOIN row for the "My Bookings" list: bookings + events + venues + tickets."""

    id: int
    status: BookingStatus
    created_at: str
    cancelled_at: str | None
    ticket_code: str
    event_id: int
    event_title: str
    event_status: EventStatus
    event_start_time: str
    event_end_time: str
    venue_id: int
    venue_name: str


@dataclass(frozen=True)
class BookingSeatBriefRow:
    """Seat summary row in the booking list; `booking_id` is used to group seats back into their bookings."""

    booking_id: int
    seat_id: int
    row_number: int
    seat_number: int
    seat_type: SeatType


class VenueBrief(BaseModel):
    id: int
    name: str


class EventSummary(BaseModel):
    """Event summary inlined in a booking; fields align with the EventSummary in api.md §4.1."""

    id: int
    title: str
    status: EventStatus
    startTime: str
    endTime: str
    venue: VenueBrief


class SeatBrief(BaseModel):
    id: int
    row: int
    number: int
    label: str
    seatType: SeatType


class BookingPublic(BaseModel):
    id: int
    status: BookingStatus
    createdAt: str
    cancelledAt: str | None
    ticketCode: str
    event: EventSummary
    seats: list[SeatBrief]


class BookingPage(BaseModel):
    items: list[BookingPublic]
    total: int
    page: int
    pageSize: int


class CreateBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventId: Annotated[int, Field(strict=True, gt=0)]
    seatIds: Annotated[list[Annotated[int, Field(strict=True, gt=0)]], Field(min_length=1)]


class CancelBookingPayload(BaseModel):
    id: int
    status: Literal["cancelled"]
    cancelledAt: str
