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
    cover_url: str
    logo_url: str
    rating_average: float | None  # 新增：平均分
    rating_count: int             # 新增：评分人数


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
    cover_url: str = Field(default="", alias="coverUrl")
    logo_url: str = Field(default="", alias="logoUrl")
    rating_average: float | None = Field(default=None, alias="ratingAverage")  # 新增
    rating_count: int = Field(default=0, alias="ratingCount")                  # 新增


class EventListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyword: str | None = None
    statuses: list[ActivityStatus] = []
    ended: bool | None = None
    organizer_id: int | None = None
    page: int = 1
    page_size: int = 20


class CreateEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: str
    description: str
    start_time: str
    end_time: str
    venue_id: int | None = None
    cover_url: str = Field(default="", alias="coverUrl")
    logo_url: str = Field(default="", alias="logoUrl")


class UpdateEventStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["published", "closed", "cancelled"]