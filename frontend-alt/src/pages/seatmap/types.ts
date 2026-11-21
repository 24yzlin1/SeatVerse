// Identifiers follow the contract's positive integers; display labels and
// array indexes are never used as business ids.
export type SeatId = number;
export type EventId = number;
export type VenueId = number;

// docs/contracts/enums.md: the first version only has standard seats; the
// `locked` value is reserved and never selectable.
export type SeatType = "standard";
export type EventSeatStatus = "available" | "locked" | "sold";
export type EventStatus = "draft" | "published" | "closed" | "cancelled";

// Static venue coordinates are adopted verbatim from the backend: meters,
// X points right, Y points up, Z points from the stage towards the rear.
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

// Dynamic data never duplicates coordinates; entries link to `StaticSeat.id`
// through `seatId`.
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

// Local selection only; it is not server state and never means a seat hold.
export type SelectedSeatIds = ReadonlySet<SeatId>;

export type SeatVisualState = "available" | "sold" | "selected" | "unavailable";
export type SeatPalette = Readonly<Record<SeatVisualState, string>>;

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
}

export interface SeatMapData {
  readonly event: SeatSelectionEvent & {
    readonly description: string;
    readonly venue: VenueSummary & { readonly capacity: number };
  };
  readonly seats: readonly StaticSeat[];
  readonly seatStates: ReadonlyMap<SeatId, EventSeatStatus>;
}
