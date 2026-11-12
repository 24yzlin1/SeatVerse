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
    """电子票查询的 JOIN 行：tickets + bookings + events + venues。"""

    ticket_id: int
    booking_id: int
    ticket_code: str
    verified_at: str | None
    verified_by: int | None
    booking_status: BookingStatus
    booking_created_at: str
    event_id: int
    event_title: str
    event_status: EventStatus
    event_start_time: str
    event_end_time: str
    venue_id: int
    venue_name: str


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
