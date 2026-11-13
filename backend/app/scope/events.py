from typing import Callable

from fastapi import APIRouter, Depends
from app.core.common import AppError
from app.core.events import (
    get_event_detail as get_event_detail_core,
    update_event_status as update_event_status_core,
)
from app.core.events import list_events as list_events_core
from app.scope.common import ok
from app.types.common import PaginatedPayload, ResponsePayload
from app.types.events import (
    ActivityStatus,
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


@router.get("")
def list_events(
    keyword: str | None = None,
    status: ActivityStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ResponsePayload[dict[str, object]]:
    if page < 1:
        raise AppError(400, "Page must be at least 1")
    if page_size < 1 or page_size > _MAXIMUM_PAGE_SIZE:
        raise AppError(400, f"Page size must be between 1 and {_MAXIMUM_PAGE_SIZE}")
    normalized_keyword = keyword.strip() if keyword is not None else None
    if normalized_keyword == "":
        normalized_keyword = None
    query = EventListQuery(
        keyword=normalized_keyword,
        status=status,
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
