/**
 * 错误码 → 文案。
 *
 * 设计目标：所有面向用户的中文文案集中在本文件，页面与组件里不得出现裸错误串。
 * 硬性口径（01—05）：
 *   1) 业务结果只看响应体 `code`，不得依赖 HTTP 状态码（02 §三、03 §六、04 §3.1）；
 *   2) 后端 `message` 已保证可直接展示，前端一律原样使用（02 §三、03 §六、04 §3.1）；
 *   3) 只有后端 `message` 为空时才用错误码兜底，禁止按接口特化改写文案。
 *
 * 动作不在本文件：401 的清令牌与跳转由请求客户端实现（见 docs/contracts/auth.md §7）。
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

/** 所有兜底都未命中时的最终文案。 */
export const FALLBACK_MESSAGE = "操作失败，请稍后重试";

/**
 * 取最终展示文案。
 *
 * 优先级只有一条：后端 `message` 非空就原样使用；为空才按 `code` 兜底。
 * 不再提供按接口路径的特化表：02 §三 / 03 §六 / 04 §3.1 规定场景细分由后端
 * `message` 完成。前端只保留两类 409 特殊处理：选座提交的 409 刷新座位状态并提示重选；
 * 重复签到的 409 由核验页按 03 §8 展示首次签到时间。其余 409 只展示后端 `message`。
 */
export function resolveMessage(code: number, serverMessage?: string): string {
  if (serverMessage !== undefined && serverMessage.trim().length > 0) {
    return serverMessage;
  }
  return CODE_MESSAGE[code] ?? FALLBACK_MESSAGE;
}
