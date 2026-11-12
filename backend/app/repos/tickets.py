"""电子票的数据库访问。

当前只实现预约事务需要的 `insert_ticket`；电子票查询、核验与状态派生由 F 的
`repos/tickets.py` / `core/tickets.py` 继续扩展。本函数只写 SQL，不 commit、不 close。
"""

import sqlite3

from app.repos.database import (
    DatabaseConnection,
    fetch_one_row,
    read_integer,
    read_optional_integer,
    read_optional_text,
    read_text,
)
from app.types.tickets import TicketRow


def _row_to_ticket(row: sqlite3.Row) -> TicketRow:
    return TicketRow(
        id=read_integer(row, "id"),
        booking_id=read_integer(row, "booking_id"),
        ticket_code=read_text(row, "ticket_code"),
        verified_at=read_optional_text(row, "verified_at"),
        verified_by=read_optional_integer(row, "verified_by"),
    )


def insert_ticket(
    connection: DatabaseConnection, booking_id: int, ticket_code: str
) -> TicketRow:
    """在调用方的预约事务内写入一张电子票，不自行提交。"""
    cursor = connection.execute(
        "INSERT INTO tickets (booking_id, ticket_code) VALUES (?, ?)",
        (booking_id, ticket_code),
    )
    last_row_id = cursor.lastrowid
    if last_row_id is None:
        raise RuntimeError("Failed to obtain inserted ticket id")
    row = fetch_one_row(
        connection,
        "SELECT id, booking_id, ticket_code, verified_at, verified_by "
        "FROM tickets WHERE id = ?",
        (last_row_id,),
    )
    if row is None:
        raise RuntimeError("Inserted ticket row not found")
    return _row_to_ticket(row)
