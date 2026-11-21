import type {
  EventStatus,
  EventSeatStatus,
  SeatId,
  SeatMapData,
  StaticSeat,
} from "./types";
export { bookingBlockReason } from "@/common/utils/eventAvailability";

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("接口数据格式异常，请刷新后重试");
  }
  return value as Record<string, unknown>;
}

function positiveInteger(value: unknown): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 1) {
    throw new Error("接口返回了无效编号或容量");
  }
  return value;
}

function text(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error("活动或座位信息不完整");
  }
  return value;
}

function timestamp(value: unknown): string {
  const result = text(value);
  if (
    !result.includes("T") ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(result) ||
    !Number.isFinite(Date.parse(result))
  ) {
    throw new Error("活动时间缺失或格式异常");
  }
  return result;
}

function coordinate(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error("座位坐标无效，请联系场馆管理员");
  }
  return value;
}

function items(value: unknown): unknown[] {
  const result = record(value).items;
  if (!Array.isArray(result)) {
    throw new Error("座位接口未返回有效列表");
  }
  return result;
}

export function parseSeatEvent(
  value: unknown,
  expectedId: number,
): SeatMapData["event"] {
  const event = record(value);
  const id = positiveInteger(event.id);
  if (id !== expectedId) {
    throw new Error("活动编号与当前页面不一致，请重新进入活动");
  }
  const venue = record(event.venue);
  const status = event.status;
  if (
    status !== "draft" &&
    status !== "published" &&
    status !== "closed" &&
    status !== "cancelled"
  ) {
    throw new Error("活动状态未知，暂不可选座");
  }
  const startTime = timestamp(event.startTime);
  const endTime = timestamp(event.endTime);
  if (Date.parse(endTime) <= Date.parse(startTime)) {
    throw new Error("活动结束时间必须晚于开始时间");
  }
  return Object.freeze({
    id,
    title: text(event.title),
    status: status as EventStatus,
    startTime,
    endTime,
    description: typeof event.description === "string" ? event.description : "",
    venue: Object.freeze({
      id: positiveInteger(venue.id),
      name: text(venue.name),
      capacity: positiveInteger(venue.capacity),
    }),
  });
}

export function adaptSeatMap(
  eventValue: unknown,
  staticValue: unknown,
  dynamicValue: unknown,
  expectedId: number,
): SeatMapData {
  const event = parseSeatEvent(eventValue, expectedId);
  const ids = new Set<SeatId>();
  const positions = new Set<string>();
  const labels = new Set<string>();
  const seats = items(staticValue).map((value): StaticSeat => {
    const seat = record(value);
    const id = positiveInteger(seat.id);
    const row = positiveInteger(seat.row);
    const number = positiveInteger(seat.number);
    const x = coordinate(seat.x),
      y = coordinate(seat.y),
      z = coordinate(seat.z);
    const position = `${x},${y},${z}`;
    const place = `${row},${number}`;
    if (ids.has(id) || positions.has(position) || labels.has(place)) {
      throw new Error("场馆座位编号、排座或坐标重复");
    }
    if (seat.seatType !== "standard") {
      throw new Error("存在尚不支持的座位类型");
    }
    ids.add(id);
    positions.add(position);
    labels.add(place);
    return Object.freeze({
      id,
      row,
      number,
      x,
      y,
      z,
      label: text(seat.label),
      seatType: "standard",
    });
  });
  if (seats.length > 0 && seats.length !== event.venue.capacity) {
    throw new Error("场馆座位数量与容量不一致，请联系场馆管理员");
  }
  const seatStates = new Map<SeatId, EventSeatStatus>();
  for (const value of items(dynamicValue)) {
    const entry = record(value);
    const id = positiveInteger(entry.seatId);
    const status = entry.status;
    if (!ids.has(id) || seatStates.has(id)) {
      throw new Error("活动座位与场馆座位不匹配");
    }
    if (status !== "available" && status !== "sold" && status !== "locked") {
      throw new Error("座位状态未知，暂不可预约");
    }
    seatStates.set(id, status);
  }
  if (
    (event.status === "published" || event.status === "closed") &&
    seatStates.size !== seats.length
  ) {
    throw new Error("本场座位状态不完整，请刷新或联系活动主办方");
  }
  return { event, seats: Object.freeze(seats), seatStates };
}
