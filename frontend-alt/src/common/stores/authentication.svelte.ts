// Login session store (authentication state).
//
// Implements docs/contracts/auth.md §3-§10 item by item:
//   - Key names and value format (§3): token stored verbatim, trimmed;
//     "null" / "undefined" / blank are treated as signed out and the key is
//     removed;
//   - Authority (§4): the token is the single source of truth, the user is
//     only a cache; a stored token always triggers a `me` re-fetch on boot;
//   - State machine (§5): idle → loading → authed / guest; network failures
//     keep the token and never redirect; concurrent bootstraps share one
//     in-flight promise;
//   - Write and clear (§6): setSession writes the token first, then the user;
//     clear removes the user first, then the token, uses removeItem and is
//     idempotent;
//   - 401 (§7): this store only performs clear(); redirect deduplication and
//     the exempt path list live in restClient.ts;
//   - Cross-tab (§8): only the storage event is observed; the event payload
//     is never trusted, the token is always re-read;
//   - Degradation (§9): when localStorage is unavailable the store falls back
//     to memory state with a single warning; invalid JSON removes the key;
//     late responses are discarded.
//
// HTTP stays out of this file: the request client (including the
// Authorization injection and envelope parsing) is injected through
// `setAuthenticationApi()`. auth.md §14.3 keeps token injection inside
// restClient.ts only.
import { ApiError } from "@/common/api/types";
import type {
  LoginPayload,
  LoginResponse,
  Role,
  User,
} from "@/common/api/types";

// Single definition point for the storage keys (auth.md §3).
export const AUTHENTICATION_TOKEN_STORAGE_KEY =
  "seatverse.authentication.token";
export const AUTHENTICATION_USER_STORAGE_KEY = "seatverse.authentication.user";

export type AuthenticationStatus = "idle" | "loading" | "authed" | "guest";

// Snapshot read by route guards and navigation UI.
export interface AuthenticationSnapshot {
  status: AuthenticationStatus;
  role: Role | null;
}

// Injection point for the request client: the implementation owns all HTTP,
// including the `Authorization: Bearer <token>` header, the `/api` prefix,
// envelope parsing and 401 redirect deduplication.
export interface AuthenticationApi {
  me: () => Promise<User>;
  login: (payload: LoginPayload) => Promise<LoginResponse>;
}

let authenticationApi: AuthenticationApi | null = null;

export function setAuthenticationApi(api: AuthenticationApi): void {
  authenticationApi = api;
}

// ===== localStorage access (falls back to memory state when unavailable,
// auth.md §9) =====

// In-memory copy used while localStorage is unavailable (only two keys, no
// reactivity needed).
const memory: Record<string, string> = {};
let storageUsable = true;
let warned = false;

function warnOnce(message: string): void {
  if (warned) {
    return;
  }
  warned = true;
  console.warn(message);
}

function degrade(reason: unknown): void {
  storageUsable = false;
  warnOnce(
    `[authentication] localStorage is unavailable, falling back to memory state for this session: ${String(reason)}`,
  );
}

function readRaw(key: string): string | null {
  if (!storageUsable) {
    return memory[key] ?? null;
  }
  try {
    return window.localStorage.getItem(key);
  } catch (error) {
    degrade(error);
    return memory[key] ?? null;
  }
}

function writeRaw(key: string, value: string): void {
  memory[key] = value;
  if (!storageUsable) {
    return;
  }
  try {
    window.localStorage.setItem(key, value);
  } catch (error) {
    // Includes QuotaExceededError: keep going on memory state so login never
    // fails because of storage.
    degrade(error);
  }
}

function removeRaw(key: string): void {
  delete memory[key];
  if (!storageUsable) {
    return;
  }
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    degrade(error);
  }
}

// ===== Value normalization and cache parsing (auth.md §3 rules 1-2, §9
// invalid JSON) =====

function normalizeToken(raw: string | null): string | null {
  if (raw === null) {
    return null;
  }
  const value = raw.trim();
  if (value.length === 0 || value === "null" || value === "undefined") {
    return null;
  }
  return value;
}

function isUser(value: unknown): value is User {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  const role = candidate.role;
  return (
    typeof candidate.id === "number" &&
    typeof candidate.name === "string" &&
    typeof candidate.email === "string" &&
    (role === "user" || role === "organizer")
  );
}

// Read the cached user; invalid JSON removes the key and returns null so the
// application never shows a blank screen (§9).
function readUserCache(): User | null {
  const raw = readRaw(AUTHENTICATION_USER_STORAGE_KEY);
  if (raw === null) {
    return null;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    removeRaw(AUTHENTICATION_USER_STORAGE_KEY);
    return null;
  }
  if (!isUser(parsed)) {
    removeRaw(AUTHENTICATION_USER_STORAGE_KEY);
    return null;
  }
  return parsed;
}

function cacheUser(user: User | null): void {
  if (user === null) {
    removeRaw(AUTHENTICATION_USER_STORAGE_KEY);
    return;
  }
  writeRaw(AUTHENTICATION_USER_STORAGE_KEY, JSON.stringify(user));
}

// Replace the current hash address without adding a history entry. The
// router-level navigation lives outside this store, so logout and the
// cross-tab handler replace the address directly.
function replaceAddress(path: string): void {
  window.history.replaceState(null, "", `#${path}`);
}

class AuthenticationStore {
  token = $state<string | null>(null);
  user = $state<User | null>(null);
  status = $state<AuthenticationStatus>("idle");

  // Session generation: incremented by clear()/setSession() to discard late
  // `me` responses (§9, last rule).
  private epoch = 0;
  // In-flight promise shared by concurrent bootstrap calls (§5, §9).
  private inFlight: Promise<void> | null = null;

  private readonly onStorage = (): void => {
    const next = normalizeToken(readRaw(AUTHENTICATION_TOKEN_STORAGE_KEY));

    if (next === null) {
      const hadSession = this.token !== null;
      this.clear();
      if (hadSession) {
        // Another tab signed out: send this tab back to the home page as
        // well (replace, so going back cannot restore the session).
        replaceAddress("/");
      }
      return;
    }

    if (next === this.token) {
      // Only the user cache changed: ignore it, identity comes from the
      // re-fetched result (§8).
      return;
    }

    // Another tab switched the token: sync it and re-fetch the identity (§8).
    this.epoch += 1;
    this.inFlight = null;
    this.token = next;
    this.user = null;
    this.status = "loading";
    void this.bootstrap();
  };

  constructor() {
    const storedToken = normalizeToken(
      readRaw(AUTHENTICATION_TOKEN_STORAGE_KEY),
    );
    if (storedToken === null) {
      // Dirty values ("null" / "undefined" / blank) normalize to signed out
      // and the keys are removed (§3, rule 2).
      removeRaw(AUTHENTICATION_TOKEN_STORAGE_KEY);
      removeRaw(AUTHENTICATION_USER_STORAGE_KEY);
      this.user = null;
    } else {
      this.user = readUserCache();
    }
    this.token = storedToken;

    if (typeof window !== "undefined") {
      window.addEventListener("storage", this.onStorage);
    }
  }

  get isLoggedIn(): boolean {
    return this.token !== null && this.status === "authed";
  }

  // Interface visibility and route branching only; permissions are enforced
  // by the backend (auth.md §4).
  get role(): Role | null {
    return this.user?.role ?? null;
  }

  snapshot(): AuthenticationSnapshot {
    return { status: this.status, role: this.role };
  }

  // Write the session after a successful login: token first, then user (§6);
  // the user may be null and gets filled in by the bootstrap re-fetch.
  setSession(token: string, user?: User | null): void {
    const normalized = normalizeToken(token);
    if (normalized === null) {
      this.clear();
      return;
    }

    this.epoch += 1;
    this.inFlight = null;
    writeRaw(AUTHENTICATION_TOKEN_STORAGE_KEY, normalized);
    cacheUser(user ?? null);
    this.token = normalized;
    this.user = user ?? null;
    this.status = "authed";
  }

  // Sign out / invalidate: user first, then token; removeItem, idempotent,
  // no request (§6).
  clear(): void {
    this.epoch += 1;
    this.inFlight = null;
    removeRaw(AUTHENTICATION_USER_STORAGE_KEY);
    removeRaw(AUTHENTICATION_TOKEN_STORAGE_KEY);
    this.token = null;
    this.user = null;
    this.status = "guest";
  }

  // Startup re-fetch: a stored token always triggers a `me` request; network
  // failures keep the token and never redirect (§4, §5).
  async bootstrap(): Promise<void> {
    if (this.inFlight !== null) {
      return this.inFlight;
    }

    const run = this.runBootstrap();
    this.inFlight = run;
    try {
      await run;
    } finally {
      if (this.inFlight === run) {
        this.inFlight = null;
      }
    }
  }

  // Login: writes the session on success and rethrows failures (the 401
  // exempt path is handled by the request client, not duplicated here).
  async login(payload: LoginPayload): Promise<void> {
    if (authenticationApi === null) {
      throw new ApiError(0, "请求客户端尚未接入");
    }

    const epoch = this.epoch;
    this.status = "loading";
    try {
      const result = await authenticationApi.login(payload);
      if (this.epoch !== epoch) {
        return;
      }
      this.setSession(result.token, result.user);
    } catch (error) {
      if (this.epoch === epoch) {
        this.status = this.token === null ? "guest" : "authed";
      }
      throw error;
    }
  }

  // Explicit sign out: clear first, then go back to the home page, so
  // guarded routes never read a stale token (§6).
  logout(): void {
    this.clear();
    replaceAddress("/");
  }

  private async runBootstrap(): Promise<void> {
    if (this.token === null) {
      // No token means no `me` request (§5).
      this.status = "guest";
      return;
    }

    if (authenticationApi === null) {
      // Request client not injected yet: keep the token, treat as signed out
      // and warn once.
      warnOnce(
        "[authentication] request client is not wired up; a token exists but `me` cannot be re-fetched",
      );
      this.status = "guest";
      return;
    }

    const epoch = this.epoch;
    this.status = "loading";

    try {
      const user = await authenticationApi.me();
      if (this.epoch !== epoch) {
        return;
      }
      this.user = user;
      cacheUser(user);
      this.status = "authed";
    } catch (error) {
      if (this.epoch !== epoch) {
        return;
      }
      if (error instanceof ApiError && error.code === 401) {
        // Token invalidated: remove both keys (§5, §7.4).
        this.clear();
        return;
      }
      // Network failure / envelope error / other business codes: keep the
      // token and never redirect (§5, §9).
      this.status = "guest";
    }
  }
}

export const authentication: AuthenticationStore = new AuthenticationStore();
