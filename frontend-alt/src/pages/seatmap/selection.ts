import type {
  EventSeatStatus,
  SeatId,
  SeatVisualState,
  SelectedSeatIds,
  StaticSeat,
} from "./types";

export const SEAT_VISUAL_LABEL: Readonly<Record<SeatVisualState, string>> = {
  available: "可选",
  sold: "已预约",
  selected: "本地已选",
  unavailable: "锁定或状态未知，不可选",
};

// The business occupancy status always wins over the local selection; unknown
// statuses are never selectable.
export function seatVisualState(
  seatId: SeatId,
  states: ReadonlyMap<SeatId, EventSeatStatus>,
  selected: SelectedSeatIds,
): SeatVisualState {
  const state = states.get(seatId);
  if (state === "sold") {
    return "sold";
  }
  if (state !== "available") {
    return "unavailable";
  }
  return selected.has(seatId) ? "selected" : "available";
}

export function filterSelection(
  selected: SelectedSeatIds,
  seats: readonly StaticSeat[],
  states: ReadonlyMap<SeatId, EventSeatStatus>,
): SelectedSeatIds {
  return new Set(
    seats
      .filter(
        (seat) => selected.has(seat.id) && states.get(seat.id) === "available",
      )
      .map((seat) => seat.id),
  );
}

export function toggleSeatSelection(
  selected: SelectedSeatIds,
  seatId: SeatId,
  seats: readonly StaticSeat[],
  states: ReadonlyMap<SeatId, EventSeatStatus>,
): SelectedSeatIds {
  const next = new Set(filterSelection(selected, seats, states));
  if (
    !seats.some((seat) => seat.id === seatId) ||
    states.get(seatId) !== "available"
  ) {
    return next;
  }
  if (next.has(seatId)) {
    next.delete(seatId);
  } else {
    next.add(seatId);
  }
  return next;
}

export function clearSelection(): SelectedSeatIds {
  return new Set<SeatId>();
}
