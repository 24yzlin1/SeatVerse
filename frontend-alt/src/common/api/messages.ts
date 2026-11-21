// Mapping from error codes to display messages.
//
// Every user-facing Chinese message lives in this file; pages and components
// must not contain bare error strings.
// Rules:
//   1) The business result only depends on the body `code`, never on the HTTP
//      status code;
//   2) The backend `message` is guaranteed to be display-ready and is used
//      verbatim;
//   3) Only when the backend `message` is empty do we fall back by error code;
//      per-endpoint message overrides are forbidden.
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
// Single priority rule: use the backend `message` verbatim when non-empty;
// fall back by `code` only when it is empty. Fine-grained scenario text is
// produced by the backend.
export function resolveMessage(code: number, serverMessage?: string): string {
  if (serverMessage !== undefined && serverMessage.trim().length > 0) {
    return serverMessage;
  }
  return RESPONSE_CODE_MESSAGES[code] ?? FALLBACK_MESSAGE;
}
