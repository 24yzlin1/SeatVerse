from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.types.venues import VenuePublic

ActivityStatus = Literal["draft", "published", "closed", "cancelled"]


@dataclass(frozen=True)
class EventRow:
    id: int
    title: str
    description: str
    start_time: str
    end_time: str
    organizer_id: int
    venue_id: int
    status: ActivityStatus
    created_at: str


@dataclass(frozen=True)
class EventWithVenueRow:
    event: EventRow
    venue_name: str
    venue_capacity: int
    organizer_name: str


class EventPublic(BaseModel):
    id: int
    title: str
    description: str
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")
    status: ActivityStatus
    venue: VenuePublic
    organizer_name: str = Field(..., alias="organizerName")
    # The organizer frontend filters its own events by id; without this field it could only guess by name (added by F on 2026-11-17).
    organizer_id: int = Field(..., alias="organizerId")


class EventListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyword: str | None = None
    # Multi-value status filter (expanded from comma-separated input); an empty tuple means no filtering.
    statuses: list[ActivityStatus] = []
    # None means no filtering; True shows only ended events (end_time <= now and status still published/closed),
    # False shows only ongoing events (end_time > now).
    ended: bool | None = None
    # The organizer console fetches events by its own id, avoiding a full fetch followed by client-side filtering.
    organizer_id: int | None = None
    page: int = 1
    page_size: int = 20


class CreateEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: str
    description: str = ""
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")
    venue_id: int | None = Field(default=None, alias="venueId")


class UpdateEventStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["published", "closed", "cancelled"]
