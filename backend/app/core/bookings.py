"""预约创建的业务用例。

一个预约请求要同时完成五件事，且必须在一个事务里：
1. 校验活动可预约；
2. 逐个座位做条件更新（只有仍空闲才改成已售）；
3. 写 bookings；
4. 写 booking_seats；
5. 生成票号并写 tickets。

任何一步失败，`immediate_transaction` 会整体回滚，不会出现“座位卖了但没有预约/票”。
"""

import secrets
import sqlite3
from datetime import datetime, timezone

from app.core.common import AppError
from app.repos.bookings import (
    find_booking_detail,
    find_event_for_booking_in_transaction,
    insert_booking,
    insert_booking_seat,
    list_booking_seats,
)
from app.repos.database import (
    DatabaseConnection,
    get_connection,
    immediate_transaction,
)
from app.repos.seats import find_event_seat_in_transaction, mark_event_seat_sold
from app.repos.tickets import insert_ticket
from app.types.authentication import Identity
from app.types.bookings import (
    BookingEventRow,
    BookingListRow,
    BookingPublic,
    BookingSeatBriefRow,
    CreateBookingRequest,
    EventSummary,
    SeatBrief,
    VenueBrief,
)

_TICKET_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TICKET_CODE_LENGTH = 20
_MAX_TICKET_GENERATION_ATTEMPTS = 5


def _generate_ticket_code() -> str:
    return "".join(
        secrets.choice(_TICKET_ALPHABET) for _ in range(_TICKET_CODE_LENGTH)
    )


def _parse_event_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise AppError(500, "活动时间格式错误") from None
    if parsed.tzinfo is None:
        raise AppError(500, "活动时间缺少时区信息")
    return parsed


def _ensure_event_bookable(event: BookingEventRow, now: datetime) -> None:
    if event.status == "draft":
        raise AppError(400, "活动尚未发布，无法预约")
    if event.status == "closed":
        raise AppError(400, "活动已停止预约")
    if event.status == "cancelled":
        raise AppError(400, "活动已取消")

    start_time = _parse_event_time(event.start_time)
    end_time = _parse_event_time(event.end_time)
    if now >= end_time:
        raise AppError(400, "活动已结束")
    if now >= start_time:
        raise AppError(400, "活动已开始，无法预约")


def _insert_ticket_with_retry(
    connection: DatabaseConnection, booking_id: int
) -> None:
    for _ in range(_MAX_TICKET_GENERATION_ATTEMPTS):
        ticket_code = _generate_ticket_code()
        try:
            insert_ticket(connection, booking_id, ticket_code)
        except sqlite3.IntegrityError as error:
            if "ticket_code" not in str(error):
                raise
            continue
        return
    raise AppError(500, "票号生成失败，请稍后重试")


def _to_public(
    detail: BookingListRow, seat_rows: list[BookingSeatBriefRow]
) -> BookingPublic:
    booking_seats = [row for row in seat_rows if row.booking_id == detail.id]
    if not booking_seats:
        raise RuntimeError("Booking has no seats")
    return BookingPublic(
        id=detail.id,
        status=detail.status,
        createdAt=detail.created_at,
        cancelledAt=detail.cancelled_at,
        ticketCode=detail.ticket_code,
        event=EventSummary(
            id=detail.event_id,
            title=detail.event_title,
            status=detail.event_status,
            startTime=detail.event_start_time,
            endTime=detail.event_end_time,
            venue=VenueBrief(id=detail.venue_id, name=detail.venue_name),
        ),
        seats=[
            SeatBrief(
                id=row.seat_id,
                row=row.row_number,
                number=row.seat_number,
                label=f"{row.row_number}排{row.seat_number}号",
                seatType=row.seat_type,
            )
            for row in booking_seats
        ],
    )


def create_booking(
    identity: Identity, request: CreateBookingRequest
) -> BookingPublic:
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    booking_id = 0
    connection = get_connection()
    try:
        try:
            with immediate_transaction(connection):
                event = find_event_for_booking_in_transaction(
                    connection, request.eventId
                )
                if event is None:
                    raise AppError(404, "活动不存在")
                _ensure_event_bookable(event, now)

                for seat_id in request.seatIds:
                    if (
                        find_event_seat_in_transaction(
                            connection, event.event_id, seat_id
                        )
                        is None
                    ):
                        raise AppError(404, "座位不存在")
                    if not mark_event_seat_sold(
                        connection, event.event_id, seat_id
                    ):
                        raise AppError(409, "座位刚刚被预约，请重新选择")

                booking_id = insert_booking(
                    connection,
                    event.event_id,
                    identity.user_id,
                    created_at,
                )
                for seat_id in request.seatIds:
                    insert_booking_seat(
                        connection, booking_id, event.event_id, seat_id
                    )

                _insert_ticket_with_retry(connection, booking_id)
        except sqlite3.IntegrityError as error:
            if "booking_seats" in str(error):
                raise AppError(409, "座位刚刚被预约，请重新选择") from None
            raise
    finally:
        connection.close()

    detail = find_booking_detail(booking_id, identity.user_id)
    if detail is None:
        raise RuntimeError("Inserted booking row not found")
    seat_rows = list_booking_seats([booking_id])
    return _to_public(detail, seat_rows)
