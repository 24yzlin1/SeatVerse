/**
 * 活动与电子票的中文标签、派生展示态（唯一定义处）。
 *
 * 依据 docs/contracts/enums.md §4.1：页面不得各自维护一份中文标签表。
 * 预约状态标签复用 `common/utils/groupBookings.ts` 的 `STATUS_LABEL`，避免两套。
 * §2.7 的“进行中 / 已结束 / 已完成”是派生展示态，只读不写回接口。
 */
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

/** enums.md §2.7 的 EventDisplayStatus，只用于展示。 */
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

/**
 * 按 enums.md §2.7 的顺序取第一个命中项：
 * cancelled → ended → stopped → ongoing → published → draft。
 */
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
