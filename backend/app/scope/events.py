from datetime import datetime, timezone
from typing import Callable, cast

from fastapi import APIRouter, Depends, Query
from app.core.common import AppError
from app.core.events import (
    create_event as create_event_core,
    get_event_detail as get_event_detail_core,
    update_event_status as update_event_status_core,
)
from app.core.events import list_events as list_events_core
from app.scope.common import ok
from app.types.common import PaginatedPayload, ResponsePayload
from app.types.events import (
    ActivityStatus,
    CreateEventRequest,
    EventListQuery,
    EventPublic,
    UpdateEventStatusRequest,
)
from app.scope.authentication import require_identity
from app.types.authentication import Identity, UserRole

router = APIRouter(prefix="/events", tags=["events"])
_MAXIMUM_PAGE_SIZE = 100


def _serialize_event_page(
    page: PaginatedPayload[EventPublic],
) -> dict[str, object]:
    return {
        "items": page.items,
        "total": page.total,
        "page": page.page,
        "pageSize": page.page_size,
    }


def require_role(required_role: UserRole) -> Callable[[Identity], Identity]:
    def dependency(identity: Identity = Depends(require_identity)) -> Identity:
        if identity.role != required_role:
            raise AppError(403, "Forbidden")
        return identity

    return dependency


def _parse_event_time(value: str, field_label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AppError(400, f"{field_label} must be an ISO 8601 timestamp") from None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


@router.post("")
def create_event(
    body: CreateEventRequest,
    identity: Identity = Depends(require_role("organizer")),
) -> ResponsePayload[EventPublic]:
    title = body.title.strip()
    if not title:
        raise AppError(400, "Event title must not be empty")
    if len(title) > 120:
        raise AppError(400, "Event title must not exceed 120 characters")
    start_time = body.start_time.strip()
    end_time = body.end_time.strip()
    if _parse_event_time(end_time, "End time") <= _parse_event_time(
        start_time, "Start time"
    ):
        raise AppError(400, "End time must be after start time")
    if body.venue_id is not None and body.venue_id < 1:
        raise AppError(400, "Venue id must be a positive integer")
    return ok(
        create_event_core(
            identity=identity,
            title=title,
            description=body.description.strip(),
            start_time=start_time,
            end_time=end_time,
            requested_venue_id=body.venue_id,
        )
    )


@router.get("")
def list_events(
    keyword: str | None = None,
    status: str | None = None,
    ended: bool | None = None,
    organizer_id: int | None = Query(default=None, alias="organizerId"),
    page: int = 1,
    page_size: int = Query(default=20, alias="pageSize"),
) -> ResponsePayload[dict[str, object]]:
    if page < 1:
        raise AppError(400, "Page must be at least 1")
    if page_size < 1 or page_size > _MAXIMUM_PAGE_SIZE:
        raise AppError(400, f"Page size must be between 1 and {_MAXIMUM_PAGE_SIZE}")
    normalized_keyword = keyword.strip() if keyword is not None else None
    if normalized_keyword == "":
        normalized_keyword = None
    # status supports comma-separated multi-values (e.g. status=closed,cancelled); deduplicated while preserving order.
    valid_statuses = ("draft", "published", "closed", "cancelled")
    parts = [] if status is None else [part.strip() for part in status.split(",")]
    if any(part not in valid_statuses for part in parts):
        raise AppError(
            400,
            "Status only supports draft, published, closed, cancelled",
        )
    statuses: list[ActivityStatus] = [
        cast(ActivityStatus, part) for part in dict.fromkeys(parts)
    ]
    if organizer_id is not None and organizer_id < 1:
        raise AppError(400, "Organizer id must be a positive integer")
    query = EventListQuery(
        keyword=normalized_keyword,
        statuses=statuses,
        ended=ended,
        organizer_id=organizer_id,
        page=page,
        page_size=page_size,
    )
    page_result = list_events_core(query)
    return ok(_serialize_event_page(page_result))


@router.get("/{event_id}")
def get_event_detail(event_id: int) -> ResponsePayload[EventPublic]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    return ok(get_event_detail_core(event_id))


@router.patch("/{event_id}/status")
def update_event_status(
    event_id: int,
    body: UpdateEventStatusRequest,
    identity: Identity = Depends(require_role("organizer")),
) -> ResponsePayload[EventPublic]:
    if event_id < 1:
        raise AppError(400, "Event id must be a positive integer")
    return ok(
        update_event_status_core(
            identity=identity,
            event_id=event_id,
            target_status=body.status,
        )
    )
