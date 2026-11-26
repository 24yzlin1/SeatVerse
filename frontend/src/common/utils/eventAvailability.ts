import type { EventSummary } from "@/common/api/types";

type EventTiming = Pick<EventSummary, "status" | "startTime" | "endTime">;

export function bookingBlockReason(
  event: EventTiming,
  now = Date.now(),
): string {
  if (event.status === "draft") return "活动尚未发布";
  if (event.status === "closed") return "活动已停止预约";
  if (event.status === "cancelled") return "活动已取消";
  if (event.status !== "published") return "活动状态未知，暂不可预约";
  const start = Date.parse(event.startTime);
  const end = Date.parse(event.endTime);
  if (
    !Number.isFinite(start) ||
    !Number.isFinite(end) ||
    end <= start ||
    !Number.isFinite(now)
  )
    return "活动时间异常，暂不可预约";
  if (now >= end) return "活动已结束";
  if (now >= start) return "活动已开始，无法预约";
  return "";
}

export function eventStatusLabel(event: EventTiming, now = Date.now()): string {
  return bookingBlockReason(event, now) || "预约中";
}
