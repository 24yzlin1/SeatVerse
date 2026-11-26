"""Type definitions for e-tickets and verification.

Corresponding table: `tickets` (see backend/app/repos/migrations/000_schema.sql).
Corresponding contracts: docs/contracts/api.md §4.3, docs/contracts/enums.md §2.5,
         docs/contracts/ticket-qr.md §2 / §4.

Notes:
- The `tickets` table has no status column; ticket status is derived from the booking status and `verified_at`,
  so only the `TicketStatus` literal is defined here, with no new storage column;
- `TicketRow` maps one-to-one to table columns; the repos layer handles row mapping;
- `TicketDetailRow` is the JOIN row for e-ticket queries (tickets + bookings + events + venues);
  seat summaries reuse `app.types.bookings.BookingSeatBriefRow`;
- Response models use camelCase; fields match `samples/ticket.ok.json` verbatim.
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.types.bookings import (
    BookingStatus,
    EventStatus,
    EventSummary,
    SeatBrief,
)

# Uses the same set of literals as BookingStatus (enums.md §2.5); ticket status is a derived value, not persisted.
TicketStatus = Literal["reserved", "cancelled", "used"]


@dataclass(frozen=True)
class TicketRow:
    """A row of the `tickets` table; column order matches 000_schema.sql."""

    id: int
    booking_id: int
    ticket_code: str
    verified_at: str | None
    verified_by: int | None


@dataclass(frozen=True)
class TicketDetailRow:
    """JOIN row for e-ticket queries: tickets + bookings + events + venues.

    `booking_user_id` and `event_organizer_id` are ownership-check fields added by F:
    ticket-code queries need to tell "whether the ticket belongs to the requester", and verification needs to tell
    "whether the ticket belongs to an event run by this organizer".
    """

    ticket_id: int
    booking_id: int
    ticket_code: str
    verified_at: str | None
    verified_by: int | None
    booking_status: BookingStatus
    booking_created_at: str
    booking_user_id: int
    event_id: int
    event_title: str
    event_status: EventStatus
    event_start_time: str
    event_end_time: str
    event_organizer_id: int
    venue_id: int
    venue_name: str


@dataclass(frozen=True)
class RosterRow:
    """A row of the organizer roster: booking + user + ticket verification info (added by F, see tickets-roster.md)."""

    booking_id: int
    booking_status: BookingStatus
    created_at: str
    cancelled_at: str | None
    ticket_code: str | None
    user_id: int
    user_name: str
    user_email: str
    verified_at: str | None
    verified_by: int | None
    # Event summary (shows "which event was booked" when querying across events)
    event_id: int
    event_title: str
    event_status: EventStatus
    event_start_time: str
    event_end_time: str
    venue_id: int
    venue_name: str


class TicketPublic(BaseModel):
    """E-ticket response; fields align with the `Ticket` in api.md §4.3."""

    id: int
    bookingId: int
    ticketCode: str
    status: TicketStatus
    issuedAt: str
    verifiedAt: str | None
    verifiedBy: int | None
    event: EventSummary
    seats: list[SeatBrief]


class VerifyTicketRequest(BaseModel):
    """Request body of `POST /api/tickets/verify` (ticket-qr.md §4.2)."""

    model_config = ConfigDict(extra="forbid")

    ticketCode: str


class RosterUserPublic(BaseModel):
    """User summary in the roster; used for on-site checks by organizers."""

    id: int
    name: str
    email: str


class RosterEntryPublic(BaseModel):
    """A row of the event roster; fields are documented in docs/contracts/tickets-roster.md §1.3."""

    id: int
    status: BookingStatus
    createdAt: str
    cancelledAt: str | None
    ticketCode: str | None
    user: RosterUserPublic
    # Event summary: cross-event queries (username search beyond verify history) need to show the owning event
    event: EventSummary
    seats: list[SeatBrief]
    verifiedAt: str | None
    verifiedBy: int | None


@dataclass(frozen=True)
class RosterSummaryRow:
    """Statistics row of `GET /events/{id}/roster-summary` (repos layer)."""

    total: int
    reserved: int
    checked_in: int
    cancelled: int


class RosterSummaryPublic(BaseModel):
    """Roster statistics response: total bookings and counts per status."""

    total: int
    reserved: int
    checkedIn: int
    cancelled: int


class RosterPagePublic(BaseModel):
    """Structure inside the roster pagination envelope, matching `{items,total,page,pageSize}` in api.md §2."""

    items: list[RosterEntryPublic]
    total: int
    page: int
    pageSize: int


class TicketPagePublic(BaseModel):
    """Verification history pagination: ticket view (with event summary and verification info)."""

    items: list[TicketPublic]
    total: int
    page: int
    pageSize: int
