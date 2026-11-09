import type {
  EventId,
  EventSeatState,
  MockSeatEvent,
  SeatId,
  SeatSelectionEvent,
  StaticSeat,
  VenueSummary,
} from "./types";

export const mockVenue: VenueSummary = Object.freeze({
  id: 1,
  name: "SeatVerse 校园礼堂",
});

// 固定的十排、每排十二座；中央留出过道。无随机数，不随活动变化。
const columnPositions = [
  -7.1, -6, -4.9, -3.8, -2.7, -1.6, 1.6, 2.7, 3.8, 4.9, 6, 7.1,
];

export const mockSeats: readonly StaticSeat[] = Object.freeze(
  Array.from({ length: 120 }, (_, index): StaticSeat => {
    const row = Math.floor(index / 12) + 1;
    const number = (index % 12) + 1;
    return Object.freeze({
      id: index + 1,
      row,
      number,
      label: `${row}排${number}号`,
      seatType: "standard",
      x: columnPositions[number - 1],
      y: 0,
      z: Number((1.8 + (row - 1) * 1.2).toFixed(1)),
    });
  }),
);

export const mockEvents: readonly SeatSelectionEvent[] = Object.freeze([
  Object.freeze({
    id: 1001,
    title: "校园音乐会 · 秋日序曲",
    status: "published",
    startTime: "2026-12-05T19:00:00+08:00",
    endTime: "2026-12-05T21:00:00+08:00",
    venue: mockVenue,
  }),
  Object.freeze({
    id: 1002,
    title: "校园分享会 · 设计与科技",
    status: "published",
    startTime: "2026-12-06T14:00:00+08:00",
    endTime: "2026-12-06T16:00:00+08:00",
    venue: mockVenue,
  }),
]);

function createSeatStates(
  soldSeatIds: readonly SeatId[],
): readonly EventSeatState[] {
  const sold = new Set(soldSeatIds);
  return Object.freeze(
    mockSeats.map((seat): EventSeatState =>
      Object.freeze({
        seatId: seat.id,
        status: sold.has(seat.id) ? "sold" : "available",
      }),
    ),
  );
}

// 两套完整且独立的动态状态；冻结数据可防止演示过程污染下一次进入的结果。
const fixtures: readonly MockSeatEvent[] = Object.freeze([
  Object.freeze({
    event: mockEvents[0],
    seatStates: createSeatStates([
      3, 4, 15, 16, 29, 30, 43, 44, 57, 58, 71, 72, 85, 86, 99, 100, 111, 112,
    ]),
  }),
  Object.freeze({
    event: mockEvents[1],
    seatStates: createSeatStates([
      1, 2, 13, 14, 25, 26, 37, 38, 49, 50, 61, 62, 73, 74, 97, 98, 109, 110,
      117, 118, 119, 120,
    ]),
  }),
]);

/** 未知编号必须显式处理，不回退到默认活动，更不能假定其座位全部可用。 */
export function getMockEvent(eventId: EventId): MockSeatEvent | undefined {
  return fixtures.find((fixture) => fixture.event.id === eventId);
}
