// Unified REST request client.
//
// Branch order is fixed and must not be rearranged (docs/contracts/api.md §1
// for the /api prefix, §2 for the envelope, docs/contracts/auth.md §7 and
// §14.3 for the token handling):
//
//   1. Transport failure / timeout        → ApiError(0, network message)
//   2. Response is not JSON               → ApiError(-1, malformed message)
//   3. Missing code / message             → same as above
//   4. code === 200                       → return the payload
//   5. code === 401, non-exempt path      → clear the session, then throw
//                                           (the login drawer shows the
//                                           sign-in prompt through the
//                                           route guards)
//   6. code === 401, exempt path          → throw only; no cleanup (login /
//                                           register)
//   7. Any other business code            → surface the backend message,
//                                           fall back by code when missing
//   8. HTTP non-2xx / non-envelope        → same as line 2, HTTP status is
//                                           never read
//
// Constraints:
//   - Token injection happens only in this file (auth.md §14.3); pages and
//     stores must not set Authorization themselves;
//   - The client never reads or writes localStorage directly; the
//     authentication store owns persistence;
//   - Tokens are never logged.
import { authentication } from "@/common/stores/authentication.svelte";

import {
  RESPONSE_CODE_SUCCESS,
  RESPONSE_CODE_UNAUTHORIZED,
} from "./errorCodes";
import {
  MALFORMED_RESPONSE_MESSAGE,
  NETWORK_ERROR_MESSAGE,
  resolveMessage,
} from "./messages";
import { ApiError } from "./types";
import type { ResponseEnvelope } from "./responseEnvelope";

// Single definition point for the credential header (auth.md §14.3).
export const AUTHORIZATION_HEADER = "Authorization";
export const AUTHORIZATION_SCHEME = "Bearer ";

// Paths where a 401 must not clear the token (login / register), matched
// exactly and without the `/api` prefix.
const LOGIN_EXEMPT_PATHS: readonly string[] = [
  "/authentication/login",
  "/authentication/register",
];

const DEFAULT_TIMEOUT_MS = 10_000;

const BASE_URL = normalizeBase(import.meta.env.VITE_API_BASE ?? "/api");

export type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export interface RequestOptions {
  method?: HttpMethod;
  /** Serialized only when provided; ignored for GET. */
  body?: unknown;
  /** Caller-owned cancellation signal, chained with the timeout signal. */
  signal?: AbortSignal;
  /** Defaults to 10 seconds. */
  timeoutMs?: number;
}

function normalizeBase(value: string): string {
  const trimmed = value.replace(/\/+$/, "");
  return trimmed.length === 0 ? "/api" : trimmed;
}

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

function isExemptPath(path: string): boolean {
  return LOGIN_EXEMPT_PATHS.includes(path);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

// Minimal structural guard for the response envelope: `code` must be a number
// and `message` must be a string (api.md §2).
function isEnvelopeShape(value: unknown): value is ResponseEnvelope<unknown> {
  if (!isRecord(value)) {
    return false;
  }
  return typeof value.code === "number" && typeof value.message === "string";
}

// Hash-only path and query string of the current address, without the `#` and
// the origin, so it can be restored after login.
function currentTarget(): string {
  const rawHash = window.location.hash;
  const rawPath = rawHash.startsWith("#") ? rawHash.slice(1) : rawHash;
  return rawPath.length === 0 ? "/" : rawPath;
}

// Clear the session and replace the address with the login route; concurrent
// 401 responses only trigger one redirect.
function redirectToLogin(): void {
  if (isRedirectingToLogin) {
    return;
  }
  isRedirectingToLogin = true;
  const next = encodeURIComponent(currentTarget());
  authentication.clear();
  window.history.replaceState(null, "", `#/login?next=${next}`);
  // Reset on the next tick so one expiry storm redirects only once.
  setTimeout(() => {
    isRedirectingToLogin = false;
  }, 0);
}

function buildHeaders(
  path: string,
  method: HttpMethod,
  body: unknown,
): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };

  if (body !== undefined && method !== "GET") {
    headers["Content-Type"] = "application/json";
  }

  // Injection order (auth.md §14.3): exempt path → no header; no token → no
  // header; otherwise attach the Bearer scheme.
  const token = authentication.token;
  if (!isExemptPath(path) && token !== null && token.length > 0) {
    headers[AUTHORIZATION_HEADER] = `${AUTHORIZATION_SCHEME}${token}`;
  }

  return headers;
}

// Parse the envelope and branch on the business code; returns the payload on
// success.
function unwrap<T>(path: string, text: string): T {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    // When the backend has not taken over 404/422 it may return
    // {"detail": ...} or even an HTML error page.
    throw new ApiError(-1, MALFORMED_RESPONSE_MESSAGE);
  }

  if (!isEnvelopeShape(parsed)) {
    throw new ApiError(-1, MALFORMED_RESPONSE_MESSAGE);
  }

  const message = resolveMessage(parsed.code, parsed.message);

  if (parsed.code === RESPONSE_CODE_SUCCESS) {
    // The envelope shape is guarded at runtime; the payload type is
    // guaranteed by the contract and the sample fixtures, so the single
    // assertion is kept here.
    return parsed.payload as T;
  }

  if (parsed.code === RESPONSE_CODE_UNAUTHORIZED) {
    if (!isExemptPath(path)) {
      // The token is invalid: remove the session so the route guards switch
      // to the sign-in prompt (auth.md §7).
      authentication.clear();
    }
    throw new ApiError(RESPONSE_CODE_UNAUTHORIZED, message);
  }

  throw new ApiError(parsed.code, message);
}

// Send a request and return the unwrapped payload.
//
// @param path route path without the `/api` prefix, taken from `endpoints`
export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
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
      body:
        method === "GET" || options.body === undefined
          ? undefined
          : JSON.stringify(options.body),
      signal: controller.signal,
    });

    // Deliberately does not read response.ok / status: non-2xx HTTP responses
    // must still be parsed as an envelope.
    const text = await response.text();
    return unwrap<T>(target, text);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // fetch rejection, AbortError (timeout / cancellation) and stream read
    // failures are all treated as transport-layer failures.
    throw new ApiError(0, NETWORK_ERROR_MESSAGE);
  } finally {
    clearTimeout(timer);
    if (options.signal !== undefined) {
      options.signal.removeEventListener("abort", onAbort);
    }
  }
}
