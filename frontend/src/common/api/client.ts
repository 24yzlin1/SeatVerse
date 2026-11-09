/**
 * 统一请求客户端。
 *
 * 依据 docs/contracts/api.md §1（/api 前缀）、§2（统一信封）与 docs/contracts/auth.md §7、§14.3，
 * 分支顺序**不许调换**：先判传输层，再判结构，最后判业务码。
 *
 *   1. 传输失败 / 超时        → ApiError(0,  网络失败文案)
 *   2. 响应非 JSON            → ApiError(-1, 格式异常文案)
 *   3. 缺 code / message      → 同上
 *   4. code === 200           → 返回 payload
 *   5. code === 401 非白名单  → 去重后清令牌 + 跳登录，再抛错
 *   6. code === 401 白名单    → 只抛错，不清令牌、不跳转（登录/注册）
 *   7. 其它业务码             → 显示后端 message，缺失时按 code 兜底
 *   8. HTTP 非 2xx / 非信封   → 与第 2 行相同，**不看 status**
 *
 * 约束：
 *   - 令牌注入只在本文件发生（auth.md §14.3），页面与 store 不得自行设置 Authorization；
 *   - 只读 store，不读写 localStorage（auth.md §6）；
 *   - 绝不打印令牌（auth.md §10）。
 */
import { navigate, router } from "@/common/router";
import { auth } from "@/common/stores/auth.svelte";

import { CODE } from "./codes";
import { MALFORMED_RESPONSE_MESSAGE, NETWORK_ERROR_MESSAGE, resolveMessage } from "./messages";
import { ApiError } from "./types";
import type { Envelope } from "./types";

/** 唯一定义处（auth.md §14.3）。 */
export const AUTH_HEADER = "Authorization";
export const AUTH_SCHEME = "Bearer ";

/** 401 时不清令牌、不跳转的路径（不含 `/api` 前缀，精确匹配）。 */
const AUTH_EXEMPT_PATHS: readonly string[] = [
  "/authentication/login",
  "/authentication/register",
];

const DEFAULT_TIMEOUT_MS = 10_000;

const BASE_URL = normalizeBase(import.meta.env.VITE_API_BASE ?? "/api");

export type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export interface RequestOptions {
  method?: HttpMethod;
  /** 有值才序列化；GET 忽略。 */
  body?: unknown;
  /** 调用方自带的取消信号，与超时信号串联。 */
  signal?: AbortSignal;
  /** 默认 10 秒。 */
  timeoutMs?: number;
}

/** 同一波 401 只跳一次（auth.md §7.2 第 3 条）。 */
let redirecting = false;

function normalizeBase(value: string): string {
  const trimmed = value.replace(/\/+$/, "");
  return trimmed.length === 0 ? "/api" : trimmed;
}

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

function isExempt(path: string): boolean {
  return AUTH_EXEMPT_PATHS.includes(path);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** 统一信封的最小结构守卫：`code` 必须是 number，`message` 必须是 string（api.md §2）。 */
function isEnvelope(value: unknown): value is Envelope<unknown> {
  if (!isRecord(value)) {
    return false;
  }
  return typeof value.code === "number" && typeof value.message === "string";
}

/** auth.md §7.2：只取 hash 的路径与查询串，不含 `#` 与 origin。 */
function currentTarget(): string {
  const query = router.query.toString();
  return query.length > 0 ? `${router.path}?${query}` : router.path;
}

/** 清令牌并跳登录；并发 401 只生效一次。 */
function redirectToLogin(): void {
  if (redirecting) {
    return;
  }
  redirecting = true;
  const next = encodeURIComponent(currentTarget());
  auth.clear();
  navigate(`/login?next=${next}`, { replace: true });
  // 让同一次“过期风暴”只跳一次，下一轮导航再复位。
  setTimeout(() => {
    redirecting = false;
  }, 0);
}

function buildHeaders(path: string, method: HttpMethod, body: unknown): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };

  if (body !== undefined && method !== "GET") {
    headers["Content-Type"] = "application/json";
  }

  // 注入顺序（auth.md §14.3）：白名单 → 不注入；无令牌 → 不注入；其余带 Bearer 前缀。
  const token = auth.token;
  if (!isExempt(path) && token !== null && token.length > 0) {
    headers[AUTH_HEADER] = `${AUTH_SCHEME}${token}`;
  }

  return headers;
}

/** 解析信封并按业务码分流；成功返回 payload。 */
function unwrap<T>(path: string, text: string): T {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    // 后端未接管 404/422 时会回 {"detail": ...}，甚至 HTML 错误页。
    throw new ApiError(-1, MALFORMED_RESPONSE_MESSAGE);
  }

  if (!isEnvelope(parsed)) {
    throw new ApiError(-1, MALFORMED_RESPONSE_MESSAGE);
  }

  const message = resolveMessage(parsed.code, parsed.message);

  if (parsed.code === CODE.OK) {
    // 信封已在运行时守卫；业务字段由契约与 samples/ 保证，断言收口在此一处。
    return parsed.payload as T;
  }

  if (parsed.code === CODE.UNAUTHORIZED) {
    if (!isExempt(path)) {
      redirectToLogin();
    }
    throw new ApiError(CODE.UNAUTHORIZED, message);
  }

  throw new ApiError(parsed.code, message);
}

/**
 * 发起请求并返回解包后的 payload。
 *
 * @param path 不含 `/api` 前缀的路径，来自 `endpoints`
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const target = normalizePath(path);

  const controller = new AbortController();
  const timer = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  const onAbort = (): void => {
    controller.abort();
  };

  if (options.signal !== undefined) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener("abort", onAbort);
    }
  }

  try {
    const response = await fetch(`${BASE_URL}${target}`, {
      method,
      headers: buildHeaders(target, method, options.body),
      body: method === "GET" || options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });

    // 故意不读 response.ok / status：HTTP 非 2xx 也必须按信封解析。
    const text = await response.text();
    return unwrap<T>(target, text);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // fetch reject、AbortError（超时/取消）、读流失败，统一按传输层失败处理。
    throw new ApiError(0, NETWORK_ERROR_MESSAGE);
  } finally {
    clearTimeout(timer);
    if (options.signal !== undefined) {
      options.signal.removeEventListener("abort", onAbort);
    }
  }
}
