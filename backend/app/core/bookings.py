"""Booking creation, own-booking queries, and cancellation use cases.

A single booking request must complete five things, all within one transaction:
1. validate that the event is bookable;
2. perform conditional updates per seat (only flip to sold if still available);
3. write bookings;
4. write booking_seats;
5. generate the ticket code and write tickets.

If any step fails, `immediate_transaction` rolls everything back, so a seat can
never end up "sold without a booking/ticket".
"""

import secrets
import sqlite3
from datetime import datetime, timezone

from app.core.common import AppError
from app.repos.bookings import (
    find_booking_detail,
    find_event_for_booking_in_transaction,
    insert_booking,
    insert_booking_seat,
    list_booking_seats,
    list_user_bookings,
    find_booking_in_transaction,
    active_booking_seat_ids,
    mark_booking_cancelled,
    deactivate_booking_seats,
)
from app.repos.database import (
    DatabaseConnection,
    get_connection,
    immediate_transaction,
)
from app.repos.seats import (
    find_event_seat_in_transaction,
    mark_event_seat_sold,
    release_event_seat,
)
from app.repos.tickets import insert_ticket
from app.types.authentication import Identity
from app.types.bookings import (
    BookingEventRow,
    BookingListRow,
    BookingPublic,
    BookingSeatBriefRow,
    CreateBookingRequest,
    EventSummary,
    SeatBrief,
    VenueBrief,
    BookingPage,
    CancelBookingPayload,
    BookingStatus,
)

_TICKET_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TICKET_CODE_LENGTH = 20
_MAX_TICKET_GENERATION_ATTEMPTS = 5


def list_my_bookings(
    identity: Identity, page: int, page_size: int,
    event_id: int | None = None, status: str | None = None,
) -> BookingPage:
    if event_id is not None and event_id < 1:
        raise AppError(400, "Event ID must be a positive integer")
    allowed: dict[str, BookingStatus] = {"reserved": "reserved", "used": "used", "cancelled": "cancelled"}
    parts = [] if status is None else [part.strip() for part in status.split(",")]
    if any(part not in allowed for part in parts):
        raise AppError(400, "Booking status only supports reserved, used, cancelled")
    statuses: tuple[BookingStatus, ...] = tuple(
        dict.fromkeys(allowed[part] for part in parts)
    )
    rows, total = list_user_bookings(
        identity.user_id, page_size, (page - 1) * page_size, event_id, statuses,
    )
    seats = list_booking_seats([row.id for row in rows])
    return BookingPage(
        items=[_to_public(row, seats) for row in rows],
        total=total,
        page=page,
        pageSize=page_size,
    )


def cancel_booking(identity: Identity, booking_id: int) -> CancelBookingPayload:
    connection = get_connection()
    try:
        with immediate_transaction(connection):
            now = datetime.now(timezone.utc)
            cancelled_at = now.isoformat()
            booking = find_booking_in_transaction(connection, booking_id)
            if booking is None:
                raise AppError(404, "Booking not found")
            if booking.user_id != identity.user_id:
                raise AppError(403, "You can only cancel your own bookings")
            if booking.status != "reserved":
                raise AppError(409, "Booking is already cancelled or checked in; it cannot be cancelled again")
            event = find_event_for_booking_in_transaction(connection, booking.event_id)
            if event is None:
                raise AppError(404, "Event not found")
            if now >= _parse_event_time(event.start_time):
                raise AppError(400, "Event has already started or ended; the booking cannot be cancelled")
            if not mark_booking_cancelled(connection, booking.id, cancelled_at):
                raise AppError(409, "Booking status has changed; cancellation failed")
            seat_ids = active_booking_seat_ids(connection, booking.id)
            if not seat_ids:
                raise AppError(500, "Booking seat records are incomplete")
            for seat_id in seat_ids:
                if not release_event_seat(connection, booking.event_id, seat_id):
                    raise AppError(409, "Seat status has changed; please refresh and try again")
            deactivate_booking_seats(connection, booking.id)
    finally:
        connection.close()
    return CancelBookingPayload(
        id=booking_id, status="cancelled", cancelledAt=cancelled_at
    )


def _generate_ticket_code() -> str:
    return "".join(
        secrets.choice(_TICKET_ALPHABET) for _ in range(_TICKET_CODE_LENGTH)
    )


def _parse_event_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise AppError(500, "Event time format is invalid") from None
    if parsed.tzinfo is None:
        raise AppError(500, "Event time is missing timezone information")
    return parsed


def _ensure_event_bookable(event: BookingEventRow, now: datetime) -> None:
    if event.status == "draft":
        raise AppError(400, "Event is not published yet; booking is not allowed")
    if event.status == "closed":
        raise AppError(400, "Event has stopped taking bookings")
    if event.status == "cancelled":
        raise AppError(400, "Event is cancelled")

    start_time = _parse_event_time(event.start_time)
    end_time = _parse_event_time(event.end_time)
    if now >= end_time:
        raise AppError(400, "Event has ended")
    if now >= start_time:
        raise AppError(400, "Event has already started; booking is not allowed")


def _insert_ticket_with_retry(
    connection: DatabaseConnection, booking_id: int
) -> None:
    for _ in range(_MAX_TICKET_GENERATION_ATTEMPTS):
        ticket_code = _generate_ticket_code()
        try:
            insert_ticket(connection, booking_id, ticket_code)
        except sqlite3.IntegrityError as error:
            if "ticket_code" not in str(error):
                raise
            continue
        return
    raise AppError(500, "Failed to generate ticket code; please try again later")


def _to_public(
    detail: BookingListRow, seat_rows: list[BookingSeatBriefRow]
) -> BookingPublic:
    booking_seats = [row for row in seat_rows if row.booking_id == detail.id]
    if not booking_seats:
        raise RuntimeError("Booking has no seats")
    return BookingPublic(
        id=detail.id,
        status=detail.status,
        createdAt=detail.created_at,
        cancelledAt=detail.cancelled_at,
        ticketCode=detail.ticket_code,
        event=EventSummary(
            id=detail.event_id,
            title=detail.event_title,
            status=detail.event_status,
            startTime=detail.event_start_time,
            endTime=detail.event_end_time,
            venue=VenueBrief(id=detail.venue_id, name=detail.venue_name),
        ),
        seats=[
            SeatBrief(
                id=row.seat_id,
                row=row.row_number,
                number=row.seat_number,
                label=f"Row {row.row_number} Seat {row.seat_number}",
                seatType=row.seat_type,
            )
            for row in booking_seats
        ],
    )


def create_booking(
    identity: Identity, request: CreateBookingRequest
) -> BookingPublic:
    booking_id = 0
    connection = get_connection()
    try:
        try:
            with immediate_transaction(connection):
                now = datetime.now(timezone.utc)
                created_at = now.isoformat()
                event = find_event_for_booking_in_transaction(
                    connection, request.eventId
                )
                if event is None:
                    raise AppError(404, "Event not found")
                _ensure_event_bookable(event, now)

                for seat_id in request.seatIds:
                    if (
                        find_event_seat_in_transaction(
                            connection, event.event_id, seat_id
                        )
                        is None
                    ):
                        raise AppError(404, "Seat not found")
                    if not mark_event_seat_sold(
                        connection, event.event_id, seat_id
                    ):
                        raise AppError(409, "Seat was just booked; please choose again")

                booking_id = insert_booking(
                    connection,
                    event.event_id,
                    identity.user_id,
                    created_at,
                )
                for seat_id in request.seatIds:
                    insert_booking_seat(
                        connection, booking_id, event.event_id, seat_id
                    )

                _insert_ticket_with_retry(connection, booking_id)
        except sqlite3.IntegrityError as error:
            if "booking_seats" in str(error):
                raise AppError(409, "Seat was just booked; please choose again") from None
            raise
    finally:
        connection.close()

    detail = find_booking_detail(booking_id, identity.user_id)
    if detail is None:
        raise RuntimeError("Inserted booking row not found")
    seat_rows = list_booking_seats([booking_id])
    return _to_public(detail, seat_rows)
