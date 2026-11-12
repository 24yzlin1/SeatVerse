"""预约、预约座位与“我的预约”的类型定义。

对应表：`bookings`、`booking_seats`（见 backend/app/repos/migrations/000_schema.sql）。
对应契约：docs/contracts/api.md §4.1 / §4.2、docs/contracts/enums.md §2.2 / §2.4。

约定：
- `*Row` 是 repos 层向外暴露的数据行，字段与查询列一一对应；
- `*Public` / `*Payload` 是响应模型，JSON 键名按钉死的样例使用 camelCase；
- 时间字段一律是带时区偏移的 ISO 8601 字符串，类型层不做解析。
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.types.seats import SeatType

EventStatus = Literal["draft", "published", "closed", "cancelled"]
BookingStatus = Literal["reserved", "cancelled", "used"]


@dataclass(frozen=True)
class BookingRow:
    """`bookings` 表的一行。"""

    id: int
    event_id: int
    user_id: int
    status: BookingStatus
    created_at: str
    cancelled_at: str | None


@dataclass(frozen=True)
class BookingSeatRow:
    """`booking_seats` 表的一行。

    `is_active` 在数据库里是 INTEGER 0/1，repos 行映射时显式转成 bool；
    只有 `is_active = 1` 的记录参与占座与唯一约束。
    """

    id: int
    booking_id: int
    event_id: int
    seat_id: int
    is_active: bool


@dataclass(frozen=True)
class BookingEventRow:
    """预约事务内读取的活动信息（同一连接，不经过 D 的 events repo）。"""

    event_id: int
    status: EventStatus
    start_time: str
    end_time: str
    venue_id: int


@dataclass(frozen=True)
class BookingListRow:
    """“我的预约”列表的 JOIN 行：bookings + events + venues + tickets。"""

    id: int
    status: BookingStatus
    created_at: str
    cancelled_at: str | None
    ticket_code: str
    event_id: int
    event_title: str
    event_status: EventStatus
    event_start_time: str
    event_end_time: str
    venue_id: int
    venue_name: str


@dataclass(frozen=True)
class BookingSeatBriefRow:
    """预约列表里的座位摘要行；`booking_id` 用于把座位分回各预约。"""

    booking_id: int
    seat_id: int
    row_number: int
    seat_number: int
    seat_type: SeatType


class VenueBrief(BaseModel):
    id: int
    name: str


class EventSummary(BaseModel):
    """预约内联的活动摘要；字段与 api.md §4.1 的 EventSummary 对齐。"""

    id: int
    title: str
    status: EventStatus
    startTime: str
    endTime: str
    venue: VenueBrief


class SeatBrief(BaseModel):
    id: int
    row: int
    number: int
    label: str
    seatType: SeatType


class BookingPublic(BaseModel):
    id: int
    status: BookingStatus
    createdAt: str
    cancelledAt: str | None
    ticketCode: str
    event: EventSummary
    seats: list[SeatBrief]


class BookingPage(BaseModel):
    items: list[BookingPublic]
    total: int
    page: int
    pageSize: int


class CreateBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventId: int
    seatIds: list[int]


class CancelBookingPayload(BaseModel):
    id: int
    status: Literal["cancelled"]
    cancelledAt: str
