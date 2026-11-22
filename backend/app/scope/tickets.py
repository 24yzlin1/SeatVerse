"""Ticketing routes (owned by F).

Paths correspond one-to-one to docs/contracts/api.md §3 #14—#17; paths in `@router` do not include `/api`;
mounting is handled uniformly by the `api_router` in main.py.

This module spans three resource prefixes (`/bookings`, `/tickets`, `/events`), so the router has no prefix,
avoiding a clash with E's bookings router and D's events router over the same prefix.
"""

from fastapi import APIRouter, Depends, Query

from app.core.common import AppError
from app.core.tickets import (
    event_roster_summary as event_roster_summary_core,
    get_ticket_by_booking_id as get_ticket_by_booking_id_core,
    get_ticket_by_code as get_ticket_by_code_core,
    list_event_roster as list_event_roster_core,
    list_verify_history as list_verify_history_core,
    search_bookings_by_username as search_bookings_by_username_core,
    verify_ticket as verify_ticket_core,
)
from app.scope.authentication import require_identity
from app.scope.common import ok
from app.types.authentication import Identity
from app.types.common import ResponsePayload
from app.types.tickets import (
    RosterPagePublic,
    RosterSummaryPublic,
    TicketPagePublic,
    TicketPublic,
    VerifyTicketRequest,
)

router = APIRouter(tags=["tickets"])

_MAXIMUM_PAGE_SIZE = 100


def _require_organizer(identity: Identity = Depends(require_identity)) -> Identity:
    """Returns 403 when the role is insufficient; ticket and event ownership checks are handled as 404 in the core layer (ticket-qr.md §4.2)."""
    if identity.role != "organizer":
        raise AppError(403, "Only organizers can perform this action")
    return identity


def _validate_pagination(page: int, page_size: int) -> None:
    if page < 1:
        raise AppError(400, "page must be at least 1")
    if page_size < 1 or page_size > _MAXIMUM_PAGE_SIZE:
        raise AppError(400, f"pageSize must be between 1 and {_MAXIMUM_PAGE_SIZE}")


@router.post("/tickets/verify")
def verify_ticket(
    body: VerifyTicketRequest,
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[TicketPublic]:
    return ok(
        verify_ticket_core(identity, body.ticketCode),
        message="Verification succeeded; check-in completed",
    )


@router.get("/tickets/{ticket_code}")
def get_ticket_by_code(
    ticket_code: str,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[TicketPublic]:
    return ok(get_ticket_by_code_core(identity, ticket_code))


@router.get("/bookings/{booking_id}/ticket")
def get_booking_ticket(
    booking_id: int,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[TicketPublic]:
    if booking_id < 1:
        raise AppError(400, "Booking id must be a positive integer")
    return ok(get_ticket_by_booking_id_core(identity, booking_id))


@router.get("/events/{event_id}/bookings")
def list_event_bookings(
    event_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = Query(default=20, alias="pageSize"),
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[RosterPagePublic]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    _validate_pagination(page, page_size)
    return ok(list_event_roster_core(identity, event_id, status, page, page_size))


@router.get("/events/{event_id}/roster-summary")
def event_roster_summary(
    event_id: int,
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[RosterSummaryPublic]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    return ok(event_roster_summary_core(identity, event_id))


@router.get("/tickets/verify/history")
def list_verify_history(
    event_id: int | None = Query(default=None, alias="eventId"),
    verified_from: str | None = Query(default=None, alias="verifiedFrom"),
    verified_to: str | None = Query(default=None, alias="verifiedTo"),
    page: int = 1,
    page_size: int = Query(default=20, alias="pageSize"),
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[TicketPagePublic]:
    """Verification history persistence: records stay traceable after a page refresh, and only events owned by the requester are visible."""
    _validate_pagination(page, page_size)
    return ok(
        list_verify_history_core(
            identity, event_id, verified_from, verified_to, page, page_size
        )
    )


@router.get("/bookings/search")
def search_bookings_by_username(
    username: str,
    page: int = 1,
    page_size: int = Query(default=20, alias="pageSize"),
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[RosterPagePublic]:
    """Fuzzy-search all bookings and ticket states of an attendee by username (used for on-site checks by organizers)."""
    _validate_pagination(page, page_size)
    return ok(
        search_bookings_by_username_core(identity, username, page, page_size)
    )
