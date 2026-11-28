from datetime import datetime, timezone
from app.core.common import AppError
from app.repos.ratings import (
    find_my_rating, 
    rating_summary, 
    upsert_rating,
    has_user_booked_event,
)
from app.repos.events import find_event_by_id
from app.types.authentication import Identity
from app.types.ratings import EventRatingSummary


def get_rating_summary(event_id: int, identity: Identity | None = None) -> EventRatingSummary:
    row = find_event_by_id(event_id)
    if row is None:
        raise AppError(404, "Event not found")

    average, count = rating_summary(event_id)
    
    my_score = None
    if identity is not None:
        my_rating = find_my_rating(event_id, identity.user_id)
        if my_rating is not None:
            my_score = my_rating.score

    return EventRatingSummary(average=average, count=count, myScore=my_score)


def rate_event(identity: Identity, event_id: int, score: int) -> EventRatingSummary:
    row = find_event_by_id(event_id)
    if row is None:
        raise AppError(404, "Event not found")
        
    now_iso = datetime.now(timezone.utc).isoformat()
    if row.event.end_time > now_iso:
        raise AppError(400, "Can only rate events that have ended")

    if not has_user_booked_event(event_id, identity.user_id):
        raise AppError(403, "You must have booked this event to rate it")

    upsert_rating(event_id, identity.user_id, score, now_iso)
    
    return get_rating_summary(event_id, identity)