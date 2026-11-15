import type { Booking, BookingStatus } from "@/common/api/types";

/** 预约列表可切换的状态 tab；“全部”之外与 BookingStatus 一一对应。 */
export type BookingTab = "all" | BookingStatus;

/** 状态徽标与 tab 共用的中文标签。 */
export const STATUS_LABEL: Record<BookingStatus, string> = {
  reserved: "待参加",
  cancelled: "已取消",
  used: "已签到",
};

/** tab 的固定顺序；角标计数与筛选都以此为准。 */
export const BOOKING_TABS: ReadonlyArray<{ key: BookingTab; label: string }> = [
  { key: "all", label: "全部" },
  { key: "reserved", label: "待参加" },
  { key: "cancelled", label: "已取消" },
  { key: "used", label: "已签到" },
];

/** 按状态筛选当前列表；只做本地分组，不发起请求。 */
export function groupBookings(items: readonly Booking[], tab: BookingTab): Booking[] {
  return tab === "all" ? [...items] : items.filter((booking) => booking.status === tab);
}

/** 统计当前列表在各 tab 下的条数；“全部”即当前列表长度。 */
export function countBookings(items: readonly Booking[]): Record<BookingTab, number> {
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
