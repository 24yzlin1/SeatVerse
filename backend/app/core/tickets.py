"""票务业务用例（F 负责）。

接口归属（docs/contracts/api.md §3 #14—#17）：

| 接口 | 规则 |
|---|---|
| `GET /bookings/{id}/ticket` | 本人票；非本人 / 不存在统一 404 |
| `GET /tickets/{ticket_code}` | 登录 + 本人票；非本人 / 不存在统一 404 |
| `GET /events/{id}/bookings` | 仅本活动主办方；他人活动按 404 |
| `POST /tickets/verify` | 登录 + 主办方 + 归属校验；重复核验 409 并回显首次时间 |

票号与二维码规则见 docs/contracts/ticket-qr.md：
- 20 位 Crockford Base32，生成用 `secrets`（E 的预约事务里调用 `insert_ticket` 写入）；
- 二维码内容就是票号原文；
- 归属失败与不存在同码同文案，避免用票号枚举探测。
"""

import re
import secrets
from datetime import datetime, timedelta, timezone

from app.core.common import AppError
from app.repos.bookings import list_booking_seats
from app.repos.database import get_connection, immediate_transaction
from app.repos.tickets import (
    count_event_roster,
    find_event_organizer_id,
    find_ticket_by_booking_id,
    find_ticket_by_code,
    list_event_roster as list_event_roster_repos,
    mark_booking_used,
    mark_ticket_verified,
)
from app.types.authentication import Identity
from app.types.bookings import BookingSeatBriefRow, EventSummary, SeatBrief, VenueBrief
from app.types.tickets import (
    RosterEntryPublic,
    RosterPagePublic,
    RosterRow,
    RosterUserPublic,
    TicketDetailRow,
    TicketPublic,
    TicketStatus,
)

#: 票号字符集与长度（ticket-qr.md §2.1）：Crockford Base32，排除 I / L / O / U。
_TICKET_CODE_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TICKET_CODE_LENGTH = 20
_TICKET_CODE_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{20}$")

#: 归属失败必须与“不存在”同文案（ticket-qr.md §4.1）。
_TICKET_NOT_FOUND_MESSAGE = "票号不存在或无权查看"
_EVENT_NOT_FOUND_MESSAGE = "活动不存在或无权查看"

#: 面向用户的提示时间统一按 +08:00 展示，与契约样例一致（api.md §4 样例为 +08:00）。
#: 数据库/接口里的 `verifiedAt` 仍是 ISO 8601 原值，只有 message 做本地化。
_DISPLAY_TIMEZONE = timezone(timedelta(hours=8))
_DISPLAY_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _format_display_time(value: str) -> str:
    """把 ISO 8601 时间转成“2026-11-17 22:27:45”。

    解析失败时原样返回，避免因为一条脏数据让 409 变成 500；
    时区固定 +08:00，不依赖服务器本地时区，保证演示机与同学机器显示一致。
    """
    try:
        parsed = _parse_timestamp(value)
    except ValueError:
        return value
    return parsed.astimezone(_DISPLAY_TIMEZONE).strftime(_DISPLAY_TIME_FORMAT)


def generate_ticket_code() -> str:
    """生成 20 位票号；唯一实现，E 的预约事务直接复用。"""
    return "".join(
        secrets.choice(_TICKET_CODE_ALPHABET) for _ in range(_TICKET_CODE_LENGTH)
    )


def normalize_ticket_code(raw_value: str) -> str:
    """去首尾空格、去连字符、转大写（ticket-qr.md §2.3）。"""
    return raw_value.strip().replace("-", "").upper()


def is_valid_ticket_code(ticket_code: str) -> bool:
    return _TICKET_CODE_PATTERN.fullmatch(ticket_code) is not None


def _parse_timestamp(value: str) -> datetime:
    """解析 ISO 8601；无时区按 UTC 处理，保证可与 `datetime.now(timezone.utc)` 比较。"""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _ticket_status(row: TicketDetailRow) -> TicketStatus:
    """派生票状态：核验优先，其次预约取消，最后待核验（enums.md §2.5）。"""
    if row.verified_at is not None or row.booking_status == "used":
        return "used"
    if row.booking_status == "cancelled":
        return "cancelled"
    return "reserved"


def _seat_briefs(seat_rows: list[BookingSeatBriefRow]) -> list[SeatBrief]:
    return [
        SeatBrief(
            id=seat.seat_id,
            row=seat.row_number,
            number=seat.seat_number,
            label=f"{seat.row_number}排{seat.seat_number}号",
            seatType=seat.seat_type,
        )
        for seat in seat_rows
    ]


def _to_ticket_public(
    row: TicketDetailRow, seat_rows: list[BookingSeatBriefRow]
) -> TicketPublic:
    return TicketPublic(
        id=row.ticket_id,
        bookingId=row.booking_id,
        ticketCode=row.ticket_code,
        status=_ticket_status(row),
        issuedAt=row.booking_created_at,
        verifiedAt=row.verified_at,
        verifiedBy=row.verified_by,
        event=EventSummary(
            id=row.event_id,
            title=row.event_title,
            status=row.event_status,
            startTime=row.event_start_time,
            endTime=row.event_end_time,
            venue=VenueBrief(id=row.venue_id, name=row.venue_name),
        ),
        seats=_seat_briefs(seat_rows),
    )


def _to_roster_entry(
    row: RosterRow, seat_rows: list[BookingSeatBriefRow]
) -> RosterEntryPublic:
    return RosterEntryPublic(
        id=row.booking_id,
        status=row.booking_status,
        createdAt=row.created_at,
        cancelledAt=row.cancelled_at,
        ticketCode=row.ticket_code,
        user=RosterUserPublic(
            id=row.user_id,
            name=row.user_name,
            email=row.user_email,
        ),
        seats=_seat_briefs(seat_rows),
        verifiedAt=row.verified_at,
        verifiedBy=row.verified_by,
    )


def get_ticket_by_booking_id(identity: Identity, booking_id: int) -> TicketPublic:
    connection = get_connection()
    try:
        row = find_ticket_by_booking_id(connection, booking_id)
        if row is None or row.booking_user_id != identity.user_id:
            raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)
    finally:
        connection.close()
    return _to_ticket_public(row, list_booking_seats([row.booking_id]))


def get_ticket_by_code(identity: Identity, raw_ticket_code: str) -> TicketPublic:
    ticket_code = normalize_ticket_code(raw_ticket_code)
    if not is_valid_ticket_code(ticket_code):
        raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)

    connection = get_connection()
    try:
        row = find_ticket_by_code(connection, ticket_code)
        if row is None or row.booking_user_id != identity.user_id:
            raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)
    finally:
        connection.close()
    return _to_ticket_public(row, list_booking_seats([row.booking_id]))


def list_event_roster(
    identity: Identity,
    event_id: int,
    page: int,
    page_size: int,
) -> RosterPagePublic:
    rows: list[RosterRow] = []
    total = 0
    connection = get_connection()
    try:
        organizer_id = find_event_organizer_id(connection, event_id)
        if organizer_id is None or organizer_id != identity.user_id:
            raise AppError(404, _EVENT_NOT_FOUND_MESSAGE)
        offset = (page - 1) * page_size
        rows = list_event_roster_repos(connection, event_id, page_size, offset)
        total = count_event_roster(connection, event_id)
    finally:
        connection.close()

    seat_rows = list_booking_seats([row.booking_id for row in rows])
    seats_by_booking: dict[int, list[BookingSeatBriefRow]] = {}
    for seat in seat_rows:
        seats_by_booking.setdefault(seat.booking_id, []).append(seat)

    return RosterPagePublic(
        items=[
            _to_roster_entry(row, seats_by_booking.get(row.booking_id, []))
            for row in rows
        ],
        total=total,
        page=page,
        pageSize=page_size,
    )


def verify_ticket(identity: Identity, raw_ticket_code: str) -> TicketPublic:
    ticket_code = normalize_ticket_code(raw_ticket_code)
    if not is_valid_ticket_code(ticket_code):
        raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)

    booking_id = 0
    refreshed: TicketDetailRow | None = None
    connection = get_connection()
    try:
        with immediate_transaction(connection):
            row = find_ticket_by_code(connection, ticket_code)
            # 非本主办方活动的票与不存在同码同文案，避免枚举探测。
            if row is None or row.event_organizer_id != identity.user_id:
                raise AppError(404, _TICKET_NOT_FOUND_MESSAGE)

            if row.verified_at is not None:
                raise AppError(
                    409,
                    f"该票已于 {_format_display_time(row.verified_at)} 完成核验，不能重复签到",
                )
            if row.booking_status == "cancelled":
                raise AppError(409, "预约已取消，不能核验签到")
            if row.booking_status == "used":
                raise AppError(409, "该票已核验，不能重复签到")
            if row.event_status == "cancelled":
                raise AppError(409, "活动已取消，不能核验签到")

            now = datetime.now(timezone.utc)
            if _parse_timestamp(row.event_end_time) <= now:
                raise AppError(409, "活动已结束，不能核验签到")

            if not mark_ticket_verified(
                connection,
                ticket_id=row.ticket_id,
                verified_at=now.isoformat(),
                verified_by=identity.user_id,
            ):
                raise AppError(409, "该票刚刚已被核验，不能重复签到")
            if not mark_booking_used(connection, row.booking_id):
                raise AppError(409, "预约状态已变化，不能核验签到")
            booking_id = row.booking_id

        refreshed = find_ticket_by_code(connection, ticket_code)
    finally:
        connection.close()

    if refreshed is None:
        raise RuntimeError("Verified ticket row not found")
    return _to_ticket_public(refreshed, list_booking_seats([booking_id]))
