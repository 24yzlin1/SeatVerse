"""Ticketing business use cases (owned by F).

Endpoint ownership (docs/contracts/api.md §3 #14—#17):

| Endpoint | Rules |
|---|---|
| `GET /bookings/{id}/ticket` | Own ticket only; not owner / not found both return 404 |
| `GET /tickets/{ticket_code}` | Login + own ticket; not owner / not found both return 404 |
| `GET /events/{id}/bookings` | Organizer of this event only; other people's events return 404 |
| `POST /tickets/verify` | Login + organizer + ownership check; duplicate verification returns 409 with the first time |

Ticket code and QR code rules are in docs/contracts/ticket-qr.md:
- 20-character Crockford Base32, generated with `secrets` (E's booking transaction
  calls `insert_ticket` to persist it);
- the QR code content is the raw ticket code;
- ownership failures share the same message as "not found" to prevent enumeration
  probing via ticket codes.
"""

import re
import secrets
from datetime import datetime, timedelta, timezone

from app.core.common import AppError
from app.repos.bookings import list_booking_seats
from app.repos.database import get_connection, immediate_transaction
from app.repos.tickets import (
    count_event_roster,
    count_bookings_by_username,
    count_verified_tickets,
    event_roster_summary as event_roster_summary_repos,
    find_event_organizer_id,
    find_ticket_by_booking_id,
    find_ticket_by_code,
    list_bookings_by_username,
    list_event_roster as list_event_roster_repos,
    list_verified_tickets,
    mark_booking_used,
    mark_ticket_verified,
)
from app.types.authentication import Identity
from app.types.bookings import BookingSeatBriefRow, BookingStatus, EventSummary, SeatBrief, VenueBrief
from app.types.tickets import (
    RosterEntryPublic,
    RosterPagePublic,
    RosterRow,
    RosterSummaryPublic,
    RosterUserPublic,
    TicketDetailRow,
    TicketPagePublic,
    TicketPublic,
    TicketStatus,
)

#: Ticket code character set and length (ticket-qr.md §2.1): Crockford Base32,
#: excluding I / L / O / U.
_TICKET_CODE_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TICKET_CODE_LENGTH = 20
_TICKET_CODE_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{20}$")

#: Ownership failures must use the same message as "not found" (ticket-qr.md §4.1).
_TICKET_NOT_FOUND_MESSAGE = "Ticket not found or not authorized"
_EVENT_NOT_FOUND_MESSAGE = "Event not found or not authorized"

#: User-facing times are uniformly displayed in +08:00, consistent with the contract
#: samples (api.md §4 samples use +08:00). The `verifiedAt` in the database/API keeps
#: the raw ISO 8601 value; only the message is localized.
_DISPLAY_TIMEZONE = timezone(timedelta(hours=8))
_DISPLAY_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _format_display_time(value: str) -> str:
    """Convert an ISO 8601 time into "2026-11-17 22:27:45".

    On parse failure the raw value is returned as-is, so a single piece of bad data
    does not turn a 409 into a 500. The timezone is fixed at +08:00 and does not
    depend on the server's local timezone, keeping display consistent between the
    demo machine and teammates' machines.
    """
    try:
        parsed = _parse_timestamp(value)
    except ValueError:
        return value
    return parsed.astimezone(_DISPLAY_TIMEZONE).strftime(_DISPLAY_TIME_FORMAT)


def generate_ticket_code() -> str:
    """Generate a 20-character ticket code; the single implementation, reused
    directly by E's booking transaction."""
    return "".join(
        secrets.choice(_TICKET_CODE_ALPHABET) for _ in range(_TICKET_CODE_LENGTH)
    )


def normalize_ticket_code(raw_value: str) -> str:
    """Strip leading/trailing whitespace, remove hyphens, and uppercase
    (ticket-qr.md §2.3)."""
    return raw_value.strip().replace("-", "").upper()


def is_valid_ticket_code(ticket_code: str) -> bool:
    return _TICKET_CODE_PATTERN.fullmatch(ticket_code) is not None


def _parse_timestamp(value: str) -> datetime:
    """Parse ISO 8601; treat naive values as UTC so they can be compared with
    `datetime.now(timezone.utc)`."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _ticket_status(row: TicketDetailRow) -> TicketStatus:
    """Derive the ticket status: verification first, then booking cancellation,
    finally pending verification (enums.md §2.5)."""
    if row.verified_at is not None or row.booking_status == "used":
        return "used"
    if row.booking_status == "cancelled":
        return "cancelled"
    return "reserved"


def _seat_briefs(seat_rows: list[BookingSeatBriefRow]) -> list[SeatBrief]:
    return [
        SeatBrief(
            id=seat.seat_id,
            row=seat.row_number,
            number=seat.seat_number,
            label=f"Row {seat.row_number} Seat {seat.seat_number}",
            seatType=seat.seat_type,
        )
        for seat in seat_rows
    ]


def _to_ticket_public(
    row: TicketDetailRow, seat_rows: list[BookingSeatBriefRow]
) -> TicketPublic:
    return TicketPublic(
        id=row.ticket_id,
        bookingId=row.booking_id,
        ticketCode=row.ticket_code,
        status=_ticket_status(row),
        issuedAt=row.booking_created_at,
        verifiedAt=row.verified_at,
        verifiedBy=row.verified_by,
        event=EventSummary(
            id=row.event_id,
            title=row.event_title,
            status=row.event_status,
            startTime=row.event_start_time,
            endTime=row.event_end_time,
            venue=VenueBrief(id=row.venue_id, name=row.venue_name),
        ),
        seats=_seat_briefs(seat_rows),
    )


def _to_roster_entry(
    row: RosterRow, seat_rows: list[BookingSeatBriefRow]
) -> RosterEntryPublic:
    return RosterEntryPublic(
        id=row.booking_id,
        status=row.booking_status,
        createdAt=row.created_at,
        cancelledAt=row.cancelled_at,
        ticketCode=row.ticket_code,
        user=RosterUserPublic(
            id=row.user_id,
            name=row.user_name,
            email=row.user_email,
        ),
        event=EventSummary(
            id=row.event_id,
            title=row.event_title,
            status=row.event_status,
            startTime=row.event_start_time,
            endTime=row.event_end_time,
            venue=VenueBrief(id=row.venue_id, name=row.venue_name),
        ),
        seats=_seat_briefs(seat_rows),
        verifiedAt=row.verified_at,
        verifiedBy=row.verified_by,
    )


def get_ticket_by_booking_id(identity: Identity, booking_id: int) -> TicketPublic:
    connection = get_connection()
    try:
        row = find_ticket_by_booking_id(connection, booking_id)
        if row is None or row.booking_user_id != identity.user_id:
            raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)
    finally:
        connection.close()
    return _to_ticket_public(row, list_booking_seats([row.booking_id]))


def get_ticket_by_code(identity: Identity, raw_ticket_code: str) -> TicketPublic:
    ticket_code = normalize_ticket_code(raw_ticket_code)
    if not is_valid_ticket_code(ticket_code):
        raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)

    connection = get_connection()
    try:
        row = find_ticket_by_code(connection, ticket_code)
        if row is None or row.booking_user_id != identity.user_id:
            raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)
    finally:
        connection.close()
    return _to_ticket_public(row, list_booking_seats([row.booking_id]))


def list_event_roster(
    identity: Identity,
    event_id: int,
    status: str | None,
    page: int,
    page_size: int,
) -> RosterPagePublic:
    rows: list[RosterRow] = []
    total = 0
    statuses = _parse_booking_statuses(status)
    connection = get_connection()
    try:
        organizer_id = find_event_organizer_id(connection, event_id)
        if organizer_id is None or organizer_id != identity.user_id:
            raise AppError(404, _EVENT_NOT_FOUND_MESSAGE)
        offset = (page - 1) * page_size
        rows = list_event_roster_repos(
            connection, event_id, page_size, offset, statuses
        )
        total = count_event_roster(connection, event_id, statuses)
    finally:
        connection.close()

    return _to_roster_page(rows, total, page, page_size)


def event_roster_summary(
    identity: Identity, event_id: int
) -> RosterSummaryPublic:
    connection = get_connection()
    try:
        organizer_id = find_event_organizer_id(connection, event_id)
        if organizer_id is None or organizer_id != identity.user_id:
            raise AppError(404, _EVENT_NOT_FOUND_MESSAGE)
        summary = event_roster_summary_repos(connection, event_id)
    finally:
        connection.close()
    return RosterSummaryPublic(
        total=summary.total,
        reserved=summary.reserved,
        checkedIn=summary.checked_in,
        cancelled=summary.cancelled,
    )


def list_verify_history(
    identity: Identity,
    event_id: int | None,
    verified_from: str | None,
    verified_to: str | None,
    page: int,
    page_size: int,
) -> TicketPagePublic:
    """Persistent verification history: organizers view tickets verified for their
    own events.

    Time range inputs are normalized to UTC ISO strings before being handed to SQL
    for string comparison, matching the storage format of `verified_at`.
    """
    if event_id is not None and event_id < 1:
        raise AppError(400, "Event ID must be a positive integer")
    from_bound = (
        None
        if verified_from is None
        else _normalize_utc_iso(verified_from, "verifiedFrom")
    )
    to_bound = (
        None
        if verified_to is None
        else _normalize_utc_iso(verified_to, "verifiedTo")
    )

    rows: list[TicketDetailRow] = []
    total = 0
    connection = get_connection()
    try:
        offset = (page - 1) * page_size
        rows = list_verified_tickets(
            connection,
            identity.user_id,
            event_id,
            from_bound,
            to_bound,
            page_size,
            offset,
        )
        total = count_verified_tickets(
            connection, identity.user_id, event_id, from_bound, to_bound
        )
    finally:
        connection.close()

    seat_rows = list_booking_seats([row.booking_id for row in rows])
    seats_by_booking: dict[int, list[BookingSeatBriefRow]] = {}
    for seat in seat_rows:
        seats_by_booking.setdefault(seat.booking_id, []).append(seat)

    return TicketPagePublic(
        items=[
            _to_ticket_public(row, seats_by_booking.get(row.booking_id, []))
            for row in rows
        ],
        total=total,
        page=page,
        pageSize=page_size,
    )


def search_bookings_by_username(
    identity: Identity,
    keyword: str,
    page: int,
    page_size: int,
) -> RosterPagePublic:
    """Fuzzy-search bookings by username (organizer view), returning all bookings
    with their ticket verification info."""
    normalized = keyword.strip()
    if not normalized:
        raise AppError(400, "Username keyword must not be empty")
    if len(normalized) > 60:
        raise AppError(400, "Username keyword is too long")

    connection = get_connection()
    try:
        offset = (page - 1) * page_size
        rows = list_bookings_by_username(
            connection, normalized, page_size, offset
        )
        total = count_bookings_by_username(connection, normalized)
    finally:
        connection.close()
    return _to_roster_page(rows, total, page, page_size)


def _parse_booking_statuses(status: str | None) -> tuple[BookingStatus, ...]:
    allowed: dict[str, BookingStatus] = {
        "reserved": "reserved",
        "used": "used",
        "cancelled": "cancelled",
    }
    parts = [] if status is None else [part.strip() for part in status.split(",")]
    if any(part not in allowed for part in parts):
        raise AppError(400, "Booking status only supports reserved, used, cancelled")
    return tuple(dict.fromkeys(allowed[part] for part in parts))


def _normalize_utc_iso(value: str, field_label: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AppError(400, f"{field_label} must be an ISO 8601 time") from None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _to_roster_page(
    rows: list[RosterRow], total: int, page: int, page_size: int
) -> RosterPagePublic:
    seat_rows = list_booking_seats([row.booking_id for row in rows])
    seats_by_booking: dict[int, list[BookingSeatBriefRow]] = {}
    for seat in seat_rows:
        seats_by_booking.setdefault(seat.booking_id, []).append(seat)

    return RosterPagePublic(
        items=[
            _to_roster_entry(row, seats_by_booking.get(row.booking_id, []))
            for row in rows
        ],
        total=total,
        page=page,
        pageSize=page_size,
    )


def verify_ticket(identity: Identity, raw_ticket_code: str) -> TicketPublic:
    ticket_code = normalize_ticket_code(raw_ticket_code)
    if not is_valid_ticket_code(ticket_code):
        raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)

    booking_id = 0
    refreshed: TicketDetailRow | None = None
    connection = get_connection()
    try:
        with immediate_transaction(connection):
            row = find_ticket_by_code(connection, ticket_code)
            # Tickets of other organizers' events share the same message as "not
            # found" to prevent enumeration probing.
            if row is None or row.event_organizer_id != identity.user_id:
                raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)

            if row.verified_at is not None:
                raise AppError(
                    409,
                    f"This ticket was already verified at {_format_display_time(row.verified_at)}; check-in cannot be repeated",
                )
            if row.booking_status == "cancelled":
                raise AppError(409, "Booking is cancelled; check-in verification is not allowed")
            if row.booking_status == "used":
                raise AppError(409, "This ticket is already verified; check-in cannot be repeated")
            if row.event_status == "cancelled":
                raise AppError(409, "Event is cancelled; check-in verification is not allowed")

            now = datetime.now(timezone.utc)
            if _parse_timestamp(row.event_end_time) <= now:
                raise AppError(409, "Event has ended; check-in verification is not allowed")

            if not mark_ticket_verified(
                connection,
                ticket_id=row.ticket_id,
                verified_at=now.isoformat(),
                verified_by=identity.user_id,
            ):
                raise AppError(409, "This ticket was just verified; check-in cannot be repeated")
            if not mark_booking_used(connection, row.booking_id):
                raise AppError(409, "Booking status has changed; check-in verification is not allowed")
            booking_id = row.booking_id

        refreshed = find_ticket_by_code(connection, ticket_code)
    finally:
        connection.close()

    if refreshed is None:
        raise RuntimeError("Verified ticket row not found")
    return _to_ticket_public(refreshed, list_booking_seats([booking_id]))
