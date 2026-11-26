// Chinese labels and derived display states for events and tickets
// (single definition point).
//
// Per docs/contracts/enums.md §4.1, pages must not maintain their own label
// tables. The booking status label reuses `BOOKING_STATUS_LABEL` from
// common/utils/groupBookings.ts so there is only one copy. The "in progress"
// / "ended" / "finished" states from §2.7 are display-only and never written
// back to the API.
import type { EventStatus, TicketStatus } from "@/common/api/types";

export const EVENT_STATUS_LABEL: Record<EventStatus, string> = {
  draft: "草稿",
  published: "已发布",
  closed: "已停止预约",
  cancelled: "已取消",
};

export const TICKET_STATUS_LABEL: Record<TicketStatus, string> = {
  reserved: "待核验",
  cancelled: "已失效",
  used: "已核验",
};

// EventDisplayStatus from enums.md §2.7; display only.
export type EventDisplayStatus =
  "draft" | "published" | "ongoing" | "ended" | "stopped" | "cancelled";

export const EVENT_DISPLAY_STATUS_LABEL: Record<EventDisplayStatus, string> = {
  draft: "草稿",
  published: "已发布",
  ongoing: "进行中",
  ended: "已结束",
  stopped: "已停止预约",
  cancelled: "已取消",
};

// Three-character badge labels; the color is decided by the caller
// (primary while booking is open, destructive otherwise).
export const EVENT_SHORT_STATUS_LABEL: Record<EventDisplayStatus, string> = {
  draft: "未发布",
  published: "预约中",
  ongoing: "进行中",
  ended: "已结束",
  stopped: "已停约",
  cancelled: "已取消",
};

// Derive the display status using the §2.7 precedence order:
// cancelled → ended → stopped → ongoing → published → draft.
export function deriveEventDisplayStatus(
  event: { status: EventStatus; startTime: string; endTime: string },
  now: number = Date.now(),
): EventDisplayStatus {
  if (event.status === "cancelled") {
    return "cancelled";
  }

  const start = Date.parse(event.startTime);
  const end = Date.parse(event.endTime);
  const startKnown = !Number.isNaN(start);
  const endKnown = !Number.isNaN(end);
  const hasEnded = endKnown && now >= end;
  const isOngoing = startKnown && endKnown && start <= now && now < end;

  if ((event.status === "published" || event.status === "closed") && hasEnded) {
    return "ended";
  }
  if (event.status === "closed") {
    return "stopped";
  }
  if (event.status === "published" && isOngoing) {
    return "ongoing";
  }
  if (event.status === "published") {
    return "published";
  }
  return "draft";
}
