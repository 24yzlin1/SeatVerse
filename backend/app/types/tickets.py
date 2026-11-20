"""电子票与核验的类型定义。

对应表：`tickets`（见 backend/app/repos/migrations/000_schema.sql）。
对应契约：docs/contracts/api.md §4.3、docs/contracts/enums.md §2.5、
         docs/contracts/ticket-qr.md §2 / §4。

说明：
- `tickets` 表没有 status 列；票状态由预约状态与 `verified_at` 派生，
  因此这里只定义 `TicketStatus` 字面量，不新增存储列；
- `TicketRow` 与表列一一对应，repos 层负责行映射；
- `TicketDetailRow` 是电子票查询的 JOIN 行（tickets + bookings + events + venues），
  座位摘要复用 `app.types.bookings.BookingSeatBriefRow`；
- 响应模型使用 camelCase，字段与 `samples/ticket.ok.json` 逐字对齐。
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.types.bookings import (
    BookingStatus,
    EventStatus,
    EventSummary,
    SeatBrief,
)

# 与 BookingStatus 使用同一套字面量（enums.md §2.5）；票状态是派生值，不落库。
TicketStatus = Literal["reserved", "cancelled", "used"]


@dataclass(frozen=True)
class TicketRow:
    """`tickets` 表的一行；列顺序与 000_schema.sql 一致。"""

    id: int
    booking_id: int
    ticket_code: str
    verified_at: str | None
    verified_by: int | None


@dataclass(frozen=True)
class TicketDetailRow:
    """电子票查询的 JOIN 行：tickets + bookings + events + venues。

    `booking_user_id` 与 `event_organizer_id` 是 F 补充的归属校验字段：
    票号查询要判断“是不是本人的票”，核验要判断“是不是本主办方活动的票”。
    """

    ticket_id: int
    booking_id: int
    ticket_code: str
    verified_at: str | None
    verified_by: int | None
    booking_status: BookingStatus
    booking_created_at: str
    booking_user_id: int
    event_id: int
    event_title: str
    event_status: EventStatus
    event_start_time: str
    event_end_time: str
    event_organizer_id: int
    venue_id: int
    venue_name: str


@dataclass(frozen=True)
class RosterRow:
    """主办方名单的一行：预约 + 用户 + 票面核验信息（F 补充，见 tickets-roster.md）。"""

    booking_id: int
    booking_status: BookingStatus
    created_at: str
    cancelled_at: str | None
    ticket_code: str | None
    user_id: int
    user_name: str
    user_email: str
    verified_at: str | None
    verified_by: int | None


class TicketPublic(BaseModel):
    """电子票响应；字段与 api.md §4.3 的 `Ticket` 对齐。"""

    id: int
    bookingId: int
    ticketCode: str
    status: TicketStatus
    issuedAt: str
    verifiedAt: str | None
    verifiedBy: int | None
    event: EventSummary
    seats: list[SeatBrief]


class VerifyTicketRequest(BaseModel):
    """`POST /api/tickets/verify` 请求体（ticket-qr.md §4.2）。"""

    model_config = ConfigDict(extra="forbid")

    ticketCode: str


class RosterUserPublic(BaseModel):
    """名单里的用户摘要；主办方现场核对用。"""

    id: int
    name: str
    email: str


class RosterEntryPublic(BaseModel):
    """本场名单的一行；字段见 docs/contracts/tickets-roster.md §1.3。"""

    id: int
    status: BookingStatus
    createdAt: str
    cancelledAt: str | None
    ticketCode: str | None
    user: RosterUserPublic
    seats: list[SeatBrief]
    verifiedAt: str | None
    verifiedBy: int | None


class RosterPagePublic(BaseModel):
    """名单分页信封内的结构，与 api.md §2 的 `{items,total,page,pageSize}` 一致。"""

    items: list[RosterEntryPublic]
    total: int
    page: int
    pageSize: int
