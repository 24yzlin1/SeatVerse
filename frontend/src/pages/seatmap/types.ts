/** 编号采用契约中的正整数；不把展示标签或数组下标作为业务编号。 */
export type SeatId = number;
export type EventId = number;
export type VenueId = number;

/** docs/contracts/enums.md：第一版只有普通座，locked 预留且不可选。 */
export type SeatType = "standard";
export type EventSeatStatus = "available" | "locked" | "sold";
export type EventStatus = "draft" | "published" | "closed" | "cancelled";

/** 静态场馆坐标。模拟约定：米，X 向右、Y 向上、Z 从舞台指向后排。 */
export interface StaticSeat {
  readonly id: SeatId;
  readonly row: number;
  readonly number: number;
  readonly label: string;
  readonly seatType: SeatType;
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

/** 动态数据不重复存坐标；通过 seatId 与 StaticSeat.id 关联。 */
export interface EventSeatState {
  readonly seatId: SeatId;
  readonly status: EventSeatStatus;
}

export interface VenueSummary {
  readonly id: VenueId;
  readonly name: string;
}

export interface SeatSelectionEvent {
  readonly id: EventId;
  readonly title: string;
  readonly status: EventStatus;
  readonly startTime: string;
  readonly endTime: string;
  readonly venue: VenueSummary;
}

export interface MockSeatEvent {
  readonly event: SeatSelectionEvent;
  readonly seatStates: readonly EventSeatState[];
}

/** 仅表示本地选择，不是服务端状态，不表示锁座。 */
export type SelectedSeatIds = ReadonlySet<SeatId>;

/** 供后续场景接入；场景只通知页面，不提交预约。 */
export interface SeatInteractionCallbacks {
  readonly onSeatToggle: (seatId: SeatId) => void;
  readonly onSeatHover?: (seatId: SeatId | null) => void;
}

export interface SeatSceneProps extends SeatInteractionCallbacks {
  readonly seats: readonly StaticSeat[];
  readonly seatStates: ReadonlyMap<SeatId, EventSeatStatus>;
  readonly selectedSeatIds: SelectedSeatIds;
}
