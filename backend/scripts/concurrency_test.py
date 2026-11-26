"""Ten independent users race for the same seat over real HTTP, then results
are verified with read-only SQL."""

import argparse
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Barrier
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic import BaseModel, RootModel


class Account(BaseModel):
    email: str
    password: str


class Accounts(RootModel[list[Account]]):
    pass


class Envelope(BaseModel):
    code: int
    message: str
    payload: object = None


class UserId(BaseModel):
    id: int


class Login(BaseModel):
    token: str
    user: UserId


class Receipt(BaseModel):
    id: int


def send(
    base_url: str,
    path: str,
    token: str | None = None,
    body: object = None,
) -> Envelope:
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(base_url.rstrip("/") + path, data=data, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            raw = response.read()
    except HTTPError as error:
        raise RuntimeError(f"HTTP {error.code}: expected HTTP 200") from None
    if status != 200:
        raise RuntimeError(f"HTTP {status}: expected HTTP 200")
    return Envelope.model_validate_json(raw)


def database_state(database: Path, event_id: int, seat_id: int) -> tuple[int, int, str]:
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        row = db.execute(
            "SELECT status FROM event_seats WHERE event_id=? AND seat_id=?",
            (event_id, seat_id),
        ).fetchone()
        if row is None:
            raise RuntimeError("Target seat is missing from the specified database")
        active = db.execute(
            "SELECT COUNT(*) FROM booking_seats WHERE event_id=? AND seat_id=? AND is_active=1",
            (event_id, seat_id),
        ).fetchone()[0]
        tickets = db.execute(
            "SELECT COUNT(*) FROM tickets t JOIN booking_seats bs ON bs.booking_id=t.booking_id "
            "WHERE bs.event_id=? AND bs.seat_id=? AND bs.is_active=1",
            (event_id, seat_id),
        ).fetchone()[0]
    return int(active), int(tickets), str(row[0])


def booking_counts(database: Path, event_id: int, users: list[int]) -> tuple[int, int]:
    placeholders = ",".join("?" for _ in users)
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        bookings = db.execute(
            "SELECT COUNT(*) FROM bookings WHERE event_id=? "
            f"AND user_id IN ({placeholders})", (event_id, *users),
        ).fetchone()[0]
        tickets = db.execute(
            "SELECT COUNT(*) FROM tickets t JOIN bookings b ON b.id=t.booking_id "
            f"WHERE b.event_id=? AND b.user_id IN ({placeholders})", (event_id, *users),
        ).fetchone()[0]
    return int(bookings), int(tickets)


def run(
    base_url: str, accounts: list[Account], database: Path,
    event_id: int, seat_id: int, cleanup: bool,
) -> dict[str, int | bool]:
    if len(accounts) != 10 or len({a.email.casefold() for a in accounts}) != 10:
        raise ValueError("Exactly ten distinct accounts are required")
    if event_id < 1 or seat_id < 1:
        raise ValueError("Event and seat IDs must be positive integers")
    if database_state(database, event_id, seat_id) != (0, 0, "available"):
        raise RuntimeError("Use an initially available seat in an isolated verification database")

    logins: list[Login] = []
    for account in accounts:
        response = send(base_url, "/authentication/login", body=account.model_dump())
        if response.code != 200:
            raise RuntimeError(f"Development account login failed: business code {response.code}")
        logins.append(Login.model_validate(response.payload))
    if len({login.user.id for login in logins}) != 10:
        raise RuntimeError("Accounts must resolve to ten independent users")
    users = [login.user.id for login in logins]
    before_bookings, before_tickets = booking_counts(database, event_id, users)

    barrier = Barrier(10, timeout=30)

    def reserve(login: Login) -> Envelope:
        barrier.wait()
        return send(base_url, "/bookings", login.token, {"eventId": event_id, "seatIds": [seat_id]})

    with ThreadPoolExecutor(max_workers=10) as pool:
        responses = list(pool.map(reserve, logins))
    codes = [response.code for response in responses]
    if sorted(codes) != [200] + [409] * 9:
        raise RuntimeError(f"Expected one 200 and nine 409 responses, got {codes}")
    if database_state(database, event_id, seat_id) != (1, 1, "sold"):
        raise RuntimeError("Database must contain exactly one active occupancy and one ticket")
    if booking_counts(database, event_id, users) != (before_bookings + 1, before_tickets + 1):
        raise RuntimeError("Losing requests left extra bookings or tickets")
    winner = codes.index(200)
    booking = Receipt.model_validate(responses[winner].payload)
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        owner = db.execute(
            "SELECT b.id,b.user_id FROM bookings b JOIN booking_seats bs ON bs.booking_id=b.id "
            "WHERE bs.event_id=? AND bs.seat_id=? AND bs.is_active=1", (event_id, seat_id),
        ).fetchone()
    if owner != (booking.id, logins[winner].user.id):
        raise RuntimeError("Active occupancy does not match the successful HTTP receipt and user")

    if cleanup:
        cancelled = send(base_url, f"/bookings/{booking.id}/cancel", logins[winner].token, {})
        if cancelled.code != 200 or database_state(database, event_id, seat_id) != (0, 0, "available"):
            raise RuntimeError("Verification booking cleanup failed; check the isolated database")
    return {"http200": 10, "success": 1, "conflicts": 9, "activeOccupancy": 1, "tickets": 1, "noOrphans": True, "winnerMatched": True, "cleanedUp": cleanup}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api")
    parser.add_argument("--event-id", type=int, required=True)
    parser.add_argument("--seat-id", type=int, required=True)
    parser.add_argument("--accounts", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    try:
        accounts = Accounts.model_validate_json(args.accounts.read_text(encoding="utf-8")).root
        result = run(args.base_url, accounts, args.database, args.event_id, args.seat_id, args.cleanup)
    except ValueError:
        # Validation errors can contain raw credentials or token payloads.
        print("Concurrency verification failed: invalid accounts or response format")
        return 1
    except (OSError, RuntimeError, sqlite3.Error) as error:
        print(f"Concurrency verification failed: {error}")
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
