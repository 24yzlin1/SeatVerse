"""票务路由（F 负责）。

路径与 docs/contracts/api.md §3 #14—#17 一一对应；`@router` 内 path 不含 `/api`，
由 main.py 的 `api_router` 统一挂载。

本模块横跨 `/bookings`、`/tickets`、`/events` 三个资源前缀，因此 router 不设 prefix，
避免与 E 的 bookings router、D 的 events router 争夺同一前缀。
"""

from fastapi import APIRouter, Depends, Query

from app.core.common import AppError
from app.core.tickets import (
    get_ticket_by_booking_id as get_ticket_by_booking_id_core,
    get_ticket_by_code as get_ticket_by_code_core,
    list_event_roster as list_event_roster_core,
    verify_ticket as verify_ticket_core,
)
from app.scope.authentication import require_identity
from app.scope.common import ok
from app.types.authentication import Identity
from app.types.common import ResponsePayload
from app.types.tickets import RosterPagePublic, TicketPublic, VerifyTicketRequest

router = APIRouter(tags=["tickets"])

_MAXIMUM_PAGE_SIZE = 100


def _require_organizer(identity: Identity = Depends(require_identity)) -> Identity:
    """角色不足返回 403；票与活动的归属校验在 core 层按 404 处理（ticket-qr.md §4.2）。"""
    if identity.role != "organizer":
        raise AppError(403, "只有主办方可以执行该操作")
    return identity


def _validate_pagination(page: int, page_size: int) -> None:
    if page < 1:
        raise AppError(400, "page 必须大于等于 1")
    if page_size < 1 or page_size > _MAXIMUM_PAGE_SIZE:
        raise AppError(400, f"pageSize 必须在 1—{_MAXIMUM_PAGE_SIZE} 之间")


@router.post("/tickets/verify")
def verify_ticket(
    body: VerifyTicketRequest,
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[TicketPublic]:
    return ok(
        verify_ticket_core(identity, body.ticketCode),
        message="核验成功，签到已完成",
    )


@router.get("/tickets/{ticket_code}")
def get_ticket_by_code(
    ticket_code: str,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[TicketPublic]:
    return ok(get_ticket_by_code_core(identity, ticket_code))


@router.get("/bookings/{booking_id}/ticket")
def get_booking_ticket(
    booking_id: int,
    identity: Identity = Depends(require_identity),
) -> ResponsePayload[TicketPublic]:
    if booking_id < 1:
        raise AppError(400, "预约编号必须是正整数")
    return ok(get_ticket_by_booking_id_core(identity, booking_id))


@router.get("/events/{event_id}/bookings")
def list_event_bookings(
    event_id: int,
    page: int = 1,
    page_size: int = Query(default=20, alias="pageSize"),
    identity: Identity = Depends(_require_organizer),
) -> ResponsePayload[RosterPagePublic]:
    if event_id < 1:
        raise AppError(400, "活动编号必须是正整数")
    _validate_pagination(page, page_size)
    return ok(list_event_roster_core(identity, event_id, page, page_size))
