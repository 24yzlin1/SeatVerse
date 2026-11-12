"""座位与每场活动座位状态的类型定义。

对应表：`seats`、`event_seats`（见 backend/app/repos/migrations/000_schema.sql）。
对应枚举：docs/contracts/enums.md §2.3（EventSeatStatus）、§2.6（SeatType）。

约定：
- `*Row` 是 repos 层向外暴露的数据行，字段与表列一一对应；
- `*Public` / `*Payload` 是 scope 层返回给前端的响应模型，JSON 键名按契约使用 camelCase。
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

SeatType = Literal["standard"]
EventSeatStatus = Literal["available", "locked", "sold"]


@dataclass(frozen=True)
class SeatRow:
    """`seats` 表的一行：座位固定坐标，所有活动共用。"""

    id: int
    venue_id: int
    row_number: int
    seat_number: int
    x: float
    y: float
    z: float
    seat_type: SeatType


@dataclass(frozen=True)
class EventSeatRow:
    """`event_seats` 表的一行：某场活动中某个座位的动态状态。"""

    id: int
    event_id: int
    seat_id: int
    status: EventSeatStatus
    version: int


@dataclass(frozen=True)
class EventSeatStateRow:
    """`GET /events/{id}/seats` 的查询结果：只含动态状态，坐标由静态接口提供。"""

    seat_id: int
    status: EventSeatStatus


class SeatPublic(BaseModel):
    """静态座位响应；字段与前端 `StaticSeat` 对齐。"""

    id: int
    row: int
    number: int
    label: str
    seatType: SeatType
    x: float
    y: float
    z: float


class SeatListPayload(BaseModel):
    items: list[SeatPublic]


class EventSeatStatePublic(BaseModel):
    """动态座位响应；字段与前端 `EventSeatState` 对齐。"""

    seatId: int
    status: EventSeatStatus


class EventSeatListPayload(BaseModel):
    items: list[EventSeatStatePublic]
