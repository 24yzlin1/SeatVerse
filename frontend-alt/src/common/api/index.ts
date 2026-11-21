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
export type {
  Booking,
  BookingStatus,
  EventRecord,
  EventStatus,
  EventSummary,
  LoginPayload,
  LoginResponse,
  Page,
  Role,
  RosterEntry,
  RosterUser,
  SeatBrief,
  SeatType,
  Ticket,
  TicketStatus,
  User,
  VenueBrief,
  VenueDetail,
} from "./types";
