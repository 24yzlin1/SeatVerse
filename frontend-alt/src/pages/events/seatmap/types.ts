// Visual-scene types for the seatmap components. Domain types (SeatId,
// StaticSeat, EventSeatStatus, SeatMapData, SelectedSeatIds) come from the
// API layer via `@/common/api`; selection-state visuals (SeatVisualState,
// SeatPalette) come from `@/common/utils/seatSelection`.
import type {
  EventSeatStatus,
  SeatId,
  SelectedSeatIds,
  StaticSeat,
} from "@/common/api";
import type { SeatVisualState } from "@/common/utils/seatSelection";

// Used by scene components; scenes only notify the page and never submit
// bookings themselves.
export interface SeatInteractionCallbacks {
  readonly onSeatToggle: (seatId: SeatId) => void;
  readonly onSeatHover?: (seatId: SeatId | null) => void;
}

export interface SeatSceneProps extends SeatInteractionCallbacks {
  readonly seats: readonly StaticSeat[];
  readonly seatStates: ReadonlyMap<SeatId, EventSeatStatus>;
  readonly selectedSeatIds: SelectedSeatIds;
  readonly disabled?: boolean;
  readonly resetVersion?: number;
}
