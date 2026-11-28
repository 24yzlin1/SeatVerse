from fastapi import APIRouter, Depends
from app.core.ratings import (
    get_rating_summary as get_rating_summary_core,
    rate_event as rate_event_core,
)
from app.scope.common import ok
from app.scope.authentication import require_identity
from app.types.authentication import Identity
from app.types.common import ResponsePayload
from app.types.ratings import EventRatingSummary, RateEventRequest

router = APIRouter(prefix="/events", tags=["ratings"])


@router.get("/{event_id}/rating")
def get_rating(
    event_id: int,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[EventRatingSummary]:
    if event_id < 1:
        from app.core.common import AppError
        raise AppError(400, "Event id must be a positive integer")
    return ok(get_rating_summary_core(event_id, identity))


@router.put("/{event_id}/rating")
def rate_event(
    event_id: int,
    body: RateEventRequest,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[EventRatingSummary]:
    if event_id < 1:
        from app.core.common import AppError
        raise AppError(400, "Event id must be a positive integer")
    return ok(rate_event_core(identity, event_id, body.score))