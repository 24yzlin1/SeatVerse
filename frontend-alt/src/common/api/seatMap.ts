// Seat-map request layer: load the aggregate seat map, submit bookings and
// read seat statistics. Every response payload is strictly validated before
// it reaches a view, so renderers can trust ids, coordinates and statuses.

import { endpoints } from "./endpoints";
import { request } from "./restClient";
import { adaptSeatMap } from "./seatMapData";
import type { Booking, EventId, SeatId, SeatMapData, SeatStatistics } from "./types";

export async function loadSeatMap(
  eventId: EventId,
  signal?: AbortSignal,
): Promise<SeatMapData> {
  if (!Number.isSafeInteger(eventId) || eventId < 1) {
    throw new Error("活动编号无效，请从活动列表重新进入");
  }
  // Single aggregate request replaces the old three-call assembly
  // (event detail + venue seats + event seats).
  const payload = await request<unknown>(endpoints.eventSeatMap(eventId), {
    signal,
  });
  return adaptSeatMap(payload, eventId);
}

export async function submitBooking(
  eventId: EventId,
  seatIds: readonly SeatId[],
): Promise<Booking> {
  if (!positiveId(eventId)) {
    throw new Error("活动编号无效，请重新进入活动");
  }
  if (
    seatIds.length === 0 ||
    !seatIds.every(positiveId) ||
    new Set(seatIds).size !== seatIds.length
  ) {
    throw new Error("提交的座位无效，请重新选择");
  }
  const booking = await request<unknown>(endpoints.bookingsCreate(), {
    method: "POST",
    body: { eventId, seatIds: [...seatIds] },
  });
  if (!validBooking(booking, eventId, seatIds)) {
    throw new Error("预约已提交，但返回结果异常；请先到我的预约核对结果");
  }
  return booking;
}

export async function loadSeatStatistics(
  eventId: EventId,
  signal?: AbortSignal,
): Promise<SeatStatistics> {
  if (!positiveId(eventId)) {
    throw new Error("活动编号无效，请重新进入活动");
  }
  const value = await request<unknown>(endpoints.eventSeatStatistics(eventId), {
    signal,
  });
  if (!validStatistics(value, eventId)) {
    throw new Error("座位统计返回异常，请稍后重试");
  }
  return value;
}

function validStatistics(
  value: unknown,
  eventId: EventId,
): value is SeatStatistics {
  if (
    !record(value) ||
    value.eventId !== eventId ||
    !timestamp(value.updatedAt)
  ) {
    return false;
  }
  const counts = [value.total, value.sold, value.locked, value.available];
  if (
    !counts.every(
      (count) =>
        typeof count === "number" && Number.isSafeInteger(count) && count >= 0,
    )
  ) {
    return false;
  }
  return (
    Number(value.total) ===
    Number(value.sold) + Number(value.locked) + Number(value.available)
  );
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
  if (!record(value) || !record(value.event)) {
    return false;
  }
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
  ) {
    return false;
  }
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
    ) {
      return false;
    }
    returned.add(seat.id);
  }
  return true;
}
