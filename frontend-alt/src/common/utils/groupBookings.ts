// Local grouping helpers for the booking list.
import type { Booking, BookingStatus } from "@/common/api/types";

// Switchable status tabs of the booking list; every key except "all" maps
// one-to-one onto BookingStatus.
export type BookingTab = "all" | BookingStatus;

// Chinese label shared by the status badge and the tabs.
export const BOOKING_STATUS_LABEL: Record<BookingStatus, string> = {
  reserved: "待参加",
  cancelled: "已取消",
  used: "已签到",
};

// Fixed tab order; badge counts and filtering both follow it.
export const BOOKING_TABS: ReadonlyArray<{ key: BookingTab; label: string }> = [
  { key: "all", label: "全部" },
  { key: "reserved", label: "待参加" },
  { key: "cancelled", label: "已取消" },
  { key: "used", label: "已签到" },
];

// Filter the current list by status; purely local grouping, no request.
export function groupBookings(
  items: readonly Booking[],
  tab: BookingTab,
): Booking[] {
  return tab === "all"
    ? [...items]
    : items.filter((booking) => booking.status === tab);
}

// Count the current list entries per tab; "all" is the list length.
export function countBookings(
  items: readonly Booking[],
): Record<BookingTab, number> {
  const counts: Record<BookingTab, number> = {
    all: items.length,
    reserved: 0,
    cancelled: 0,
    used: 0,
  };

  for (const booking of items) {
    counts[booking.status] += 1;
  }

  return counts;
}
