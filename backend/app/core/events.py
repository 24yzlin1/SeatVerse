from datetime import datetime, timezone

from app.core.common import AppError
from app.repos.events import (
    count_events,
    find_event_by_id,
    find_events,
    insert_event,
    update_event_status as update_event_status_repos,
)
from app.types.common import PaginatedPayload
from app.types.events import (
    ActivityStatus,
    EventDetailPayload,
    EventListQuery,
    EventPublic,
    EventWithVenueRow,
)
from app.types.venues import VenuePublic
from app.repos.venues import find_only_venue
from app.types.authentication import Identity

_ALLOWED_STATUS_TRANSITIONS: dict[ActivityStatus, frozenset[ActivityStatus]] = {
    "draft": frozenset({"published", "cancelled"}),
    "published": frozenset({"closed", "cancelled"}),
    "closed": frozenset({"cancelled"}),
    "cancelled": frozenset(),
}


def _to_public(row: EventWithVenueRow) -> EventPublic:
    return EventPublic(
        id=row.event.id,
        title=row.event.title,
        description=row.event.description,
        start_time=row.event.start_time,
        end_time=row.event.end_time,
        status=row.event.status,
        venue=VenuePublic(
            id=row.event.venue_id,
            name=row.venue_name,
            capacity=row.venue_capacity,
        ),
        organizer_name=row.organizer_name,
    )


def _resolve_venue_id(requested_venue_id: int | None) -> int:
    only_venue = find_only_venue()
    if only_venue is None:
        raise AppError(400, "No venue is configured")
    if requested_venue_id is not None and requested_venue_id != only_venue.id:
        raise AppError(400, "Venue id must match the only configured venue")
    return only_venue.id


def list_events(query: EventListQuery) -> PaginatedPayload[EventPublic]:
    offset = (query.page - 1) * query.page_size
    rows = find_events(
        keyword=query.keyword,
        status=query.status,
        limit=query.page_size,
        offset=offset,
    )
    total = count_events(keyword=query.keyword, status=query.status)
    items = [_to_public(row) for row in rows]
    return PaginatedPayload(
        items=items,
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


def get_event_detail(event_id: int) -> EventDetailPayload:
    row = find_event_by_id(event_id)
    if row is None:
        raise AppError(404, "Event not found")
    return EventDetailPayload(event=_to_public(row))


def create_event(
    identity: Identity,
    title: str,
    description: str,
    start_time: str,
    end_time: str,
    requested_venue_id: int | None,
) -> EventDetailPayload:
    venue_id = _resolve_venue_id(requested_venue_id)
    created_at = datetime.now(timezone.utc).isoformat()
    event_id = insert_event(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        organizer_id=identity.user_id,
        venue_id=venue_id,
        status="draft",
        created_at=created_at,
    )
    row = find_event_by_id(event_id)
    if row is None:
        raise RuntimeError("Inserted event row not found")
    return EventDetailPayload(event=_to_public(row))


def update_event_status(
    identity: Identity,
    event_id: int,
    target_status: ActivityStatus,
) -> EventDetailPayload:
    row = find_event_by_id(event_id)
    if row is None:
        raise AppError(404, "Event not found")
    if row.event.organizer_id != identity.user_id:
        raise AppError(403, "Forbidden")
    current_status = row.event.status
    allowed_targets = _ALLOWED_STATUS_TRANSITIONS[current_status]
    if target_status not in allowed_targets:
        raise AppError(
            409,
            f"Cannot change event status from {current_status} to {target_status}",
        )
    updated = update_event_status_repos(
        event_id=event_id,
        organizer_id=identity.user_id,
        expected_status=current_status,
        target_status=target_status,
    )
    if not updated:
        raise AppError(409, "Event status was changed by another request")
    refreshed_row = find_event_by_id(event_id)
    if refreshed_row is None:
        raise RuntimeError("Updated event row not found")
    return EventDetailPayload(event=_to_public(refreshed_row))
