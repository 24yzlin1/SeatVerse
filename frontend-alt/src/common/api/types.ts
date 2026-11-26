// Entity and error types for the SeatVerse API.
//
// Field names follow the backend contract verbatim:
//   - Envelope and pagination: docs/contracts/api.md §2
//   - Bookings and tickets: api.md §4.1, §4.3
//   - Login and user: docs/contracts/auth.md §14.2
//   - Role and status literals: docs/contracts/enums.md §2.1-§2.6
//
// All time fields are ISO 8601 strings with a timezone offset (samples use
// `+08:00`). The frontend only renders them and never converts timezones.

// ===== Roles and status literals (enums.md) =====

// Role literal; used for interface visibility only. Permissions are enforced
// by the backend.
export type Role = "user" | "organizer";

// Booking status (enums.md §2.4). Derived display states such as "finished"
// or "in progress" are not part of this set.
export type BookingStatus = "reserved" | "cancelled" | "used";

// Ticket status (enums.md §2.5). Derived from the booking status and the
// verification result; shares the literals but not the semantics.
export type TicketStatus = "reserved" | "cancelled" | "used";

// Event status (enums.md §2.2). "In progress" and "ended" are derived from
// time and never written back.
export type EventStatus = "draft" | "published" | "closed" | "cancelled";

// Seat type (enums.md §2.6). The first version only has standard seats.
export type SeatType = "standard";

// ===== Entities (api.md §4.1 / §4.3 / auth.md §14.2) =====

export interface VenueBrief {
  id: number;
  name: string;
}

// Venue inside an event detail; carries one extra field over `VenueBrief`.
export interface VenueDetail {
  id: number;
  name: string;
  capacity: number;
}

// Event object returned by GET /events, GET /events/{id}, POST /events and
// PATCH /events/{id}/status.
//
// `organizerId` lets the organizer console filter their own events.
export interface EventRecord {
  id: number;
  title: string;
  description: string;
  /** ISO 8601 */
  startTime: string;
  /** ISO 8601 */
  endTime: string;
  status: EventStatus;
  venue: VenueDetail;
  organizerName: string;
  organizerId: number;
}

export interface EventSummary {
  id: number;
  title: string;
  status: EventStatus;
  /** ISO 8601 */
  startTime: string;
  /** ISO 8601; must be later than startTime */
  endTime: string;
  venue: VenueBrief;
}

export interface SeatBrief {
  id: number;
  /** Row number, >= 1 */
  row: number;
  /** Seat number within the row, >= 1 */
  number: number;
  /** Display label, always `Row {row} Seat {number}` */
  label: string;
  seatType: SeatType;
}

// Payload of GET /authentication/me is the user object itself, without an
// extra `{ user }` wrapper (auth.md §14.2 constraint 4).
export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
}

// Successful login and registration payload (auth.md §14.2).
export interface LoginResponse {
  token: string;
  user: User;
}

// Login request body. The contract only freezes the response (auth.md
// §14.2); the request fields follow the backend implementation
// `{ email, password }`.
export interface LoginPayload {
  email: string;
  password: string;
}

export interface Booking {
  id: number;
  status: BookingStatus;
  /** ISO 8601 */
  createdAt: string;
  /** null unless the booking is cancelled */
  cancelledAt: string | null;
  /** Inline ticket code, 20 characters; rules in docs/contracts/ticket-qr.md */
  ticketCode: string;
  event: EventSummary;
  /** At least one seat, sorted by row then number ascending */
  seats: SeatBrief[];
}

export interface Ticket {
  id: number;
  bookingId: number;
  ticketCode: string;
  status: TicketStatus;
  /** Issue time; equals the createdAt of the booking (same transaction) */
  issuedAt: string;
  /** null until verified */
  verifiedAt: string | null;
  /** User id of the verifier; null until verified */
  verifiedBy: number | null;
  event: EventSummary;
  seats: SeatBrief[];
}

// ===== Organizer roster (docs/contracts/tickets-roster.md) =====

export interface RosterUser {
  id: number;
  name: string;
  email: string;
}

export interface RosterEntry {
  /** Booking id */
  id: number;
  status: BookingStatus;
  createdAt: string;
  cancelledAt: string | null;
  /** Ticket code of the booking; legacy rows may be null */
  ticketCode: string | null;
  user: RosterUser;
  /** Event summary; lets cross-event queries show which event it belongs to */
  event: EventSummary;
  seats: SeatBrief[];
  verifiedAt: string | null;
  verifiedBy: number | null;
}

// ===== Pagination (api.md §2) =====

// Pagination structure inside a list envelope; `page` starts at 1.
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface SeatStatistics {
  eventId: number;
  total: number;
  sold: number;
  locked: number;
  available: number;
  updatedAt: string;
}

// ===== Seat map (aggregate payload of GET /events/{id}/seat-map) =====

export type SeatId = number;
export type EventId = number;

// docs/contracts/enums.md: the first version only has standard seats; the
// `locked` value is reserved and never selectable.
export type EventSeatStatus = "available" | "locked" | "sold";

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

// Event summary rendered by the seat map; `venue` carries the capacity so the
// client can cross-check the seat count.
export interface SeatSelectionEvent {
  id: EventId;
  title: string;
  status: EventStatus;
  /** ISO 8601 */
  startTime: string;
  /** ISO 8601; must be later than startTime */
  endTime: string;
  description: string;
  venue: VenueDetail;
}

// Validated aggregate payload handed to the seatmap components; frozen by the
// request layer so views cannot mutate shared data.
export interface SeatMapData {
  readonly event: SeatSelectionEvent;
  readonly seats: readonly StaticSeat[];
  readonly seatStates: ReadonlyMap<SeatId, EventSeatStatus>;
}

// Local selection only; it is not server state and never means a seat hold.
export type SelectedSeatIds = ReadonlySet<SeatId>;

// ===== Errors =====

// Unified exception thrown by the request layer.
//
// Possible `code` values:
//   0   transport failure / timeout
//   -1  response is not a valid envelope (parse failure, missing code/message)
//   any backend business code: 400 / 401 / 403 / 404 / 409
export class ApiError extends Error {
  readonly code: number;

  constructor(code: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}
