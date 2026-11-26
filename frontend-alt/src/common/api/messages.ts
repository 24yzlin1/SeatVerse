// Mapping from error codes to display messages.
//
// Every user-facing Chinese message lives in this file; pages and components
// must not contain bare error strings.
// Rules:
//   1) The business result only depends on the body `code`, never on the HTTP
//      status code;
//   2) The backend speaks English (API contract language). Known backend
//      messages are translated here into Chinese for display;
//   3) Unmapped backend messages fall back by error code, so the UI always
//      shows Chinese; per-endpoint message overrides are forbidden.
//
// Actions are not handled here: the token cleanup and the login redirect on
// 401 are implemented in restClient.ts (see docs/contracts/auth.md §7).
import {
  RESPONSE_CODE_BAD_REQUEST,
  RESPONSE_CODE_CONFLICT,
  RESPONSE_CODE_FORBIDDEN,
  RESPONSE_CODE_NOT_FOUND,
  RESPONSE_CODE_UNAUTHORIZED,
} from "./errorCodes";

// Chinese fallback messages used when the backend does not provide a
// displayable message. Covers the business codes defined by the contract.
// A 500 from the backend exception handler is not part of the contract code
// table yet, so it falls through to `FALLBACK_MESSAGE`.
export const RESPONSE_CODE_MESSAGES: Readonly<Record<number, string>> = {
  [RESPONSE_CODE_BAD_REQUEST]: "请求有误，请检查后重试",
  [RESPONSE_CODE_UNAUTHORIZED]: "登录已失效，请重新登录",
  [RESPONSE_CODE_FORBIDDEN]: "没有权限执行该操作",
  [RESPONSE_CODE_NOT_FOUND]: "请求的资源不存在",
  [RESPONSE_CODE_CONFLICT]: "操作与当前状态冲突，请刷新后重试",
};

// Translation table: backend English message (exact match) → Chinese display
// message. Keys must mirror the strings in backend/app (AppError messages and
// `ok(message=...)` texts). Dynamic f-string messages are intentionally
// unmapped and fall back by error code.
const BACKEND_MESSAGE_TRANSLATIONS: Readonly<Record<string, string>> = {
  // Authentication (scope/core authentication).
  "Invalid email format": "邮箱格式不正确",
  "Name is required": "请填写昵称",
  "Name must be at most 50 characters": "昵称不能超过 50 个字符",
  "Password is required": "请填写密码",
  "Password must be at least 8 characters": "密码至少需要 8 个字符",
  "Password must be at most 128 characters": "密码不能超过 128 个字符",
  "Please log in first": "请先登录",
  "Token expired or invalid, please log in again": "登录已失效，请重新登录",
  "Invalid session, please log in again": "登录状态无效，请重新登录",
  Forbidden: "没有权限执行该操作",
  "Email is already registered": "该邮箱已被注册",
  "Invalid email or password": "邮箱或密码不正确",
  "Session expired, please log in again": "登录已失效，请重新登录",

  // Envelope / transport produced by the backend exception handler.
  "Invalid request parameters": "请求参数格式错误",
  "Invalid JSON body": "请求体不是合法的 JSON",

  // Events.
  "Event not found": "活动不存在",
  "Event not found or not authorized": "活动不存在或无权查看",
  "Event title must not be empty": "请填写活动标题",
  "Event title must not exceed 120 characters": "活动标题不能超过 120 个字符",
  "End time must be after start time": "结束时间必须晚于开始时间",
  "Start time must be an ISO 8601 timestamp": "开始时间格式不正确",
  "End time must be an ISO 8601 timestamp": "结束时间格式不正确",
  "Venue id must be a positive integer": "场馆不存在或编号不正确",
  "Venue not found": "场馆不存在",
  "No venue is configured": "尚未配置场馆，无法创建活动",
  "Venue id must match the only configured venue": "场馆编号与已配置的场馆不一致",
  "Event status was changed by another request": "活动状态已被其他操作修改，请刷新后重试",
  "Status only supports draft, published, closed, cancelled":
    "活动状态仅支持 draft、published、closed、cancelled",

  // Seats.
  "Seat not found": "座位不存在",
  "Seat was just booked; please choose again":
    "手慢了，座位刚刚被别人约走，请重新选择",
  "Seat status has changed; please refresh and try again":
    "座位状态已变化，请刷新后重试",

  // Bookings.
  "Booking not found": "预约不存在",
  "Booking id must be a positive integer": "预约编号不正确",
  "Event id must be a positive integer": "活动编号不正确",
  "Event ID must be a positive integer": "活动编号不正确",
  "Seat id must be a positive integer": "座位编号不正确",
  "At least one seat must be selected": "请至少选择一个座位",
  "Seat ids must not be duplicated": "座位不能重复选择",
  "You can only cancel your own bookings": "只能取消自己的预约",
  "Booking is already cancelled or checked in; it cannot be cancelled again":
    "预约已取消或已核验，无法再次取消",
  "Event has already started or ended; the booking cannot be cancelled":
    "活动已开始或已结束，无法取消预约",
  "Booking status has changed; cancellation failed":
    "预约状态已变化，取消未生效，请刷新后重试",
  "Event is not published yet; booking is not allowed": "活动尚未发布，暂时无法预约",
  "Event has stopped taking bookings": "活动已停止预约",
  "Event is cancelled": "活动已取消，无法预约",
  "Event has ended": "活动已结束，无法预约",
  "Event has already started; booking is not allowed": "活动已开始，无法预约",

  // Tickets & verification.
  "Ticket not found or not authorized": "票不存在或无权查看",
  "Booking is cancelled; check-in verification is not allowed":
    "预约已取消，无法核验入场",
  "This ticket is already verified; check-in cannot be repeated":
    "该票已核验，请勿重复核验",
  "Event is cancelled; check-in verification is not allowed":
    "活动已取消，无法核验入场",
  "Event has ended; check-in verification is not allowed":
    "活动已结束，无法核验入场",
  "This ticket was just verified; check-in cannot be repeated":
    "该票刚刚已被核验，请勿重复操作",
  "Booking status has changed; check-in verification is not allowed":
    "预约状态已变化，无法核验入场",
  "Verification succeeded; check-in completed": "核验成功，签到已完成",
  "verifiedFrom must be an ISO 8601 time": "核验时间范围格式不正确",
  "verifiedTo must be an ISO 8601 time": "核验时间范围格式不正确",

  // Roster & search.
  "Only organizers can perform this action": "只有主办方可以执行该操作",
};

// Transport layer failure (network down, backend not running, timeout,
// aborted request).
export const NETWORK_ERROR_MESSAGE =
  "网络连接失败，请确认后端已启动（http://localhost:8000）";

// The response is not JSON, or is missing envelope fields such as `code` or
// `message`.
export const MALFORMED_RESPONSE_MESSAGE =
  "服务响应格式异常，请联系后端确认接口是否已实现";

// Final message when every fallback missed.
export const FALLBACK_MESSAGE = "操作失败，请稍后重试";

// Resolve the final display message.
//
// Priority: translate a known backend English message into Chinese; fall back
// by `code` for unmapped or empty backend messages, so the UI always shows
// Chinese. Fine-grained scenario text is owned by the translation table above.
export function resolveMessage(code: number, serverMessage?: string): string {
  if (serverMessage !== undefined && serverMessage.trim().length > 0) {
    return (
      BACKEND_MESSAGE_TRANSLATIONS[serverMessage.trim()] ??
      RESPONSE_CODE_MESSAGES[code] ??
      FALLBACK_MESSAGE
    );
  }
  return RESPONSE_CODE_MESSAGES[code] ?? FALLBACK_MESSAGE;
}
