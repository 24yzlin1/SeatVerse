/**
 * 接口层统一出口。
 *
 * 页面与组件只从 `@/common/api` 导入，不直接引用 `client.ts` / `codes.ts` 等相对路径，
 * 便于后续替换实现而不影响调用方（frontend-arch.md §4.3：页面不得直接调用 fetch）。
 */
export { AUTH_HEADER, AUTH_SCHEME, request } from "./client";
export { CODE } from "./codes";
export { endpoints } from "./endpoints";
export {
  CODE_MESSAGE,
  FALLBACK_MESSAGE,
  MALFORMED_RESPONSE_MESSAGE,
  NETWORK_ERROR_MESSAGE,
  resolveMessage,
} from "./messages";
export { ApiError } from "./types";
export type { HttpMethod, RequestOptions } from "./client";
export type {
  Booking,
  BookingStatus,
  Envelope,
  EventStatus,
  EventSummary,
  LoginPayload,
  LoginResponse,
  Page,
  Role,
  SeatBrief,
  SeatType,
  Ticket,
  TicketStatus,
  User,
  VenueBrief,
} from "./types";
