import { endpoints, request } from "@/common/api";
import type { Booking, BookingStatus, Page } from "@/common/api";

export interface BookingQuery {
  eventId?: number;
  status?: BookingStatus;
  page?: number;
  pageSize?: number;
}

export function loadBookingPage(
  query: BookingQuery = {},
  signal?: AbortSignal,
): Promise<Page<Booking>> {
  const params = new URLSearchParams({
    page: String(query.page ?? 1),
    pageSize: String(query.pageSize ?? 20),
  });
  if (query.eventId !== undefined) {
    params.set("eventId", String(query.eventId));
  }
  if (query.status !== undefined) {
    params.set("status", query.status);
  }
  return request<Page<Booking>>(`${endpoints.bookingsMe()}?${params}`, {
    signal,
  });
}

/** Refresh a contiguous prefix, preserving loaded depth and unique IDs. */
export async function loadBookingWindow(
  query: BookingQuery = {},
  pageCount = 1,
  signal?: AbortSignal,
): Promise<Page<Booking>> {
  let result = await loadBookingPage({ ...query, page: 1 }, signal);
  const byId = new Map(result.items.map((item) => [item.id, item]));
  for (
    let page = 2;
    page <= pageCount && (page - 1) * result.pageSize < result.total;
    page++
  ) {
    result = await loadBookingPage({ ...query, page }, signal);
    for (const item of result.items) {
      byId.set(item.id, item);
    }
  }
  return { ...result, items: [...byId.values()] };
}
