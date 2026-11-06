/**
 * 错误码 → 文案。
 *
 * 设计目标：所有面向用户的中文文案集中在本文件，页面与组件里不得出现裸错误串。
 * 取值优先级：
 *   1) 按接口路径的特化文案（如取消接口的 409）
 *   2) 后端返回的 `message`（后端已保证可直接展示）
 *   3) 错误码兜底文案
 *   4) 通用兜底文案
 *
 * 动作不在本文件：401 的清令牌与跳转由请求客户端实现（见 docs/contracts/auth.md §7），
 * 409 的刷新重试由调用页面实现。
 */
import { CODE } from "./codes";

/** 后端未给出可展示 message 时，按错误码兜底的中文文案。 */
export const CODE_MESSAGE: Readonly<Record<number, string>> = {
  [CODE.BAD_REQUEST]: "请求有误，请检查后重试",
  [CODE.UNAUTHORIZED]: "登录已失效，请重新登录",
  [CODE.FORBIDDEN]: "没有权限执行该操作",
  [CODE.NOT_FOUND]: "请求的资源不存在",
  [CODE.CONFLICT]: "操作与当前状态冲突，请刷新后重试",
  500: "服务内部异常，请稍后重试",
};

/** 传输层失败（断网、后端未启动、超时、被中断）。 */
export const NETWORK_ERROR_MESSAGE =
  "网络连接失败，请确认后端已启动（http://localhost:8000）";

/** 响应不是 JSON，或缺 `code` / `message` 等统一信封字段。 */
export const MALFORMED_RESPONSE_MESSAGE =
  "服务响应格式异常，请联系后端确认接口是否已实现";

/** HTTP 非 2xx 且无法解析出统一信封时的兜底文案。 */
export function httpErrorMessage(status: number): string {
  return `服务异常（HTTP ${status}）`;
}

/** 所有兜底都未命中时的最终文案。 */
export const FALLBACK_MESSAGE = "操作失败，请稍后重试";

/**
 * 按接口路径覆盖的文案：key 为路径模板（不含 `/api` 前缀），
 * `{name}` 匹配任意单段（如 `/bookings/42/cancel`）。
 */
const ENDPOINT_MESSAGES: Readonly<
  Record<string, Readonly<Record<number, string>>>
> = {
  "/bookings/{id}/cancel": {
    [CODE.BAD_REQUEST]: "该预约当前状态不允许取消",
    [CODE.CONFLICT]: "该预约已取消或已核验，无法再次取消",
  },
  "/tickets/{code}": {
    // 需求：不区分“不存在”和“别人的票”，避免被枚举探测
    [CODE.NOT_FOUND]: "票号不存在或无权查看",
    [CODE.FORBIDDEN]: "票号不存在或无权查看",
  },
};

const splitPath = (path: string): string[] =>
  path
    .split("?")[0]
    .split("/")
    .filter((segment) => segment.length > 0);

const matchesTemplate = (template: string, path: string): boolean => {
  const templateSegments = splitPath(template);
  const pathSegments = splitPath(path);
  if (templateSegments.length !== pathSegments.length) {
    return false;
  }
  return templateSegments.every((segment, index) => {
    const isDynamic = segment.startsWith("{") && segment.endsWith("}");
    return isDynamic || segment === pathSegments[index];
  });
};

/** 取接口路径的特化文案；没有覆盖时返回 `undefined`。 */
export function resolveEndpointMessage(
  path: string,
  code: number,
): string | undefined {
  for (const [template, messages] of Object.entries(ENDPOINT_MESSAGES)) {
    if (!matchesTemplate(template, path)) {
      continue;
    }
    const message = messages[code];
    if (message !== undefined) {
      return message;
    }
  }
  return undefined;
}

/**
 * 按上文优先级得到最终文案。
 *
 * 例：`resolveMessage("/bookings/42/cancel", 409, "座位状态冲突")`
 *     → "该预约已取消或已核验，无法再次取消"
 */
export function resolveMessage(
  path: string,
  code: number,
  serverMessage?: string,
): string {
  const endpointMessage = resolveEndpointMessage(path, code);
  if (endpointMessage !== undefined) {
    return endpointMessage;
  }
  if (serverMessage !== undefined && serverMessage.trim().length > 0) {
    return serverMessage;
  }
  return CODE_MESSAGE[code] ?? FALLBACK_MESSAGE;
}
