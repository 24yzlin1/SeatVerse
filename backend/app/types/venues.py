from dataclasses import dataclass
from pydantic import BaseModel


@dataclass(frozen=True)
class VenueRow:
    id: int
    name: str
    layout_config: str
    capacity: int


class VenuePublic(BaseModel):
    id: int
    name: str
    capacity: int


class VenuePage(BaseModel):
    items: list[VenuePublic]
    total: int
    page: int
    pageSize: int
