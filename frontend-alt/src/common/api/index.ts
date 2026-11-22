// Unified export surface for the API layer.
//
// Pages and components import only from `@/common/api` and never reference
// internal modules through relative paths, so the implementation can be
// replaced later without touching call sites.
export {
  AUTHORIZATION_HEADER,
  AUTHORIZATION_SCHEME,
  request,
} from "./restClient";
export type { HttpMethod, RequestOptions } from "./restClient";
export {
  RESPONSE_CODE_BAD_REQUEST,
  RESPONSE_CODE_CONFLICT,
  RESPONSE_CODE_FORBIDDEN,
  RESPONSE_CODE_NOT_FOUND,
  RESPONSE_CODE_SUCCESS,
  RESPONSE_CODE_UNAUTHORIZED,
} from "./errorCodes";
export { endpoints } from "./endpoints";
export {
  FALLBACK_MESSAGE,
  MALFORMED_RESPONSE_MESSAGE,
  NETWORK_ERROR_MESSAGE,
  RESPONSE_CODE_MESSAGES,
  resolveMessage,
} from "./messages";
export { ApiError } from "./types";
export type { ResponseEnvelope } from "./responseEnvelope";
export {
  loadSeatMap,
  loadSeatStatistics,
  submitBooking,
} from "./seatMap";
export { loadBookingPage, loadBookingWindow } from "./bookings";
export type { BookingQuery } from "./bookings";
export {
  SeatMapSession,
  seatMapBlockReason,
} from "./seatMapSession";
export type { SeatMapApi, SeatMapState } from "./seatMapSession";
export type {
  Booking,
  BookingStatus,
  EventId,
  EventRecord,
  EventSeatStatus,
  EventStatus,
  EventSummary,
  LoginPayload,
  LoginResponse,
  Page,
  Role,
  RosterEntry,
  RosterUser,
  SeatBrief,
  SeatId,
  SeatMapData,
  SeatSelectionEvent,
  SeatType,
  SeatStatistics,
  SelectedSeatIds,
  StaticSeat,
  Ticket,
  TicketStatus,
  User,
  VenueBrief,
  VenueDetail,
} from "./types";
