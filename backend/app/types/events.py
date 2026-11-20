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
    # 主办方前端按编号筛自己的活动；没有这个字段只能靠姓名猜（F 于 2026-11-17 补）。
    organizer_id: int = Field(..., alias="organizerId")


class EventListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyword: str | None = None
    status: ActivityStatus | None = None
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
