import { request, endpoints } from "@/common/api";
import type { Booking } from "@/common/api";
import { adaptSeatMap, parseSeatEvent } from "./data";
import type { EventId, SeatId, SeatMapData } from "./types";

export async function loadSeatMap(
  eventId: EventId,
  signal?: AbortSignal,
): Promise<SeatMapData> {
  if (!Number.isSafeInteger(eventId) || eventId < 1)
    throw new Error("活动编号无效，请从活动列表重新进入");
  const eventValue = await request<unknown>(endpoints.event(eventId), {
    signal,
  });
  const event = parseSeatEvent(eventValue, eventId);
  const [seats, states] = await Promise.all([
    request<unknown>(endpoints.venueSeats(event.venue.id), { signal }),
    request<unknown>(endpoints.eventSeats(eventId), { signal }),
  ]);
  return adaptSeatMap(eventValue, seats, states, eventId);
}

export async function submitBooking(
  eventId: EventId,
  seatIds: readonly SeatId[],
): Promise<Booking> {
  if (!positiveId(eventId)) throw new Error("活动编号无效，请重新进入活动");
  if (
    seatIds.length === 0 ||
    !seatIds.every(positiveId) ||
    new Set(seatIds).size !== seatIds.length
  )
    throw new Error("提交的座位无效，请重新选择");
  const booking = await request<unknown>(endpoints.bookingsCreate(), {
    method: "POST",
    body: { eventId, seatIds: [...seatIds] },
  });
  if (!validBooking(booking, eventId, seatIds)) {
    throw new Error("预约已提交，但返回结果异常；请先到我的预约核对结果");
  }
  return booking;
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function positiveId(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
}

function text(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function timestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.includes("T") &&
    /(?:Z|[+-]\d{2}:\d{2})$/.test(value) &&
    Number.isFinite(Date.parse(value))
  );
}

function validBooking(
  value: unknown,
  eventId: EventId,
  seatIds: readonly SeatId[],
): value is Booking {
  if (!record(value) || !record(value.event)) return false;
  const event = value.event;
  if (
    !positiveId(value.id) ||
    value.status !== "reserved" ||
    !timestamp(value.createdAt) ||
    value.cancelledAt !== null ||
    typeof value.ticketCode !== "string" ||
    !/^[0-9A-HJKMNP-TV-Z]{20}$/.test(value.ticketCode) ||
    event.id !== eventId ||
    !text(event.title) ||
    !["draft", "published", "closed", "cancelled"].includes(
      String(event.status),
    ) ||
    !timestamp(event.startTime) ||
    !timestamp(event.endTime) ||
    Date.parse(event.endTime) <= Date.parse(event.startTime) ||
    !record(event.venue) ||
    !positiveId(event.venue.id) ||
    !text(event.venue.name) ||
    !Array.isArray(value.seats) ||
    value.seats.length !== seatIds.length
  )
    return false;
  const returned = new Set<SeatId>();
  for (const seat of value.seats) {
    if (
      !record(seat) ||
      !positiveId(seat.id) ||
      !seatIds.includes(seat.id) ||
      returned.has(seat.id) ||
      !positiveId(seat.row) ||
      !positiveId(seat.number) ||
      !text(seat.label) ||
      seat.seatType !== "standard"
    )
      return false;
    returned.add(seat.id);
  }
  return true;
}
