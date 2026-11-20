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
  const booking = await request<Booking>(endpoints.bookingsCreate(), {
    method: "POST",
    body: { eventId, seatIds: [...seatIds] },
  });
  if (
    !booking ||
    !Number.isSafeInteger(booking.id) ||
    booking.id < 1 ||
    booking.event?.id !== eventId ||
    booking.status !== "reserved" ||
    !/^[0-9A-HJKMNP-TV-Z]{20}$/.test(booking.ticketCode) ||
    !Array.isArray(booking.seats) ||
    booking.seats.length !== seatIds.length ||
    booking.seats.some((seat) => !seatIds.includes(seat.id))
  ) {
    throw new Error("预约已提交，但返回结果异常；请先到我的预约核对结果");
  }
  return booking;
}
