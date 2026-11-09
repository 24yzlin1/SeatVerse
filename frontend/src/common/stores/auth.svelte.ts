/**
 * 登录态 store（会话状态）。
 *
 * 逐条实现 docs/contracts/auth.md §3—§10：
 *   - 键名与值格式（§3）：token 原文去空白；`"null"` / `"undefined"` / 空白一律视为未登录并删键；
 *   - 权威性（§4）：token 是唯一权威，user 只是缓存；启动有 token 必回源 `me`；
 *   - 状态机（§5）：idle → loading → authed / guest；网络失败保留 token 不跳转；并发共享 in-flight；
 *   - 写入与清除（§6）：setSession 先 token 后 user；clear 先 user 后 token、用 removeItem、幂等；
 *   - 401（§7）：本 store 只负责 clear()，跳转去重与白名单在请求客户端（S2-13）；
 *   - 跨标签页（§8）：只听 storage，不信 event.key，一律重读 token；
 *   - 降级（§9）：localStorage 不可用则内存态 + 一次 warn；非法 JSON 删键；迟到响应丢弃。
 *
 * 网络不进本文件：HTTP（含 Authorization 注入与信封解析）由 S2-13 的 client 负责，
 * 通过 `setAuthApi()` 注入。auth.md §14.3 规定令牌注入只发生在 client.ts 一处。
 */
import { ApiError } from "@/common/api/types";
import type { LoginPayload, LoginResponse, Role, User } from "@/common/api/types";
import { navigate } from "@/common/router";

/** auth.md §3：这两个常量唯一定义处。 */
export const TOKEN_STORAGE_KEY = "seatverse.auth.token";
export const USER_STORAGE_KEY = "seatverse.auth.user";

export type AuthStatus = "idle" | "loading" | "authed" | "guest";

/** 给路由守卫读的快照（frontend-arch.md §3.2）。 */
export interface AuthSnapshot {
  status: AuthStatus;
  role: Role | null;
}

/**
 * S2-13 注入点：实现方负责全部 HTTP，包括 `Authorization: Bearer <token>` 注入、
 * `/api` 前缀、信封解析与 401 的跳转去重。
 */
export interface AuthApi {
  me: () => Promise<User>;
  login: (payload: LoginPayload) => Promise<LoginResponse>;
}

let authApi: AuthApi | null = null;

export function setAuthApi(api: AuthApi): void {
  authApi = api;
}

// ===== localStorage 访问（不可用时降级为内存态，auth.md §9） =====

/** localStorage 不可用时的内存副本（只两个键，不需要响应式）。 */
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
  warnOnce(`[auth] localStorage 不可用，本次会话降级为内存态：${String(reason)}`);
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
    // 包含 QuotaExceededError：降级后仍以内存态继续，不能因此让登录失败。
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

// ===== 值归一与缓存解析（auth.md §3 规则 1、2；§9 非法 JSON） =====

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

/** 读 user 缓存：非法 JSON 删键后返回 null，不让应用白屏（§9）。 */
function readUserCache(): User | null {
  const raw = readRaw(USER_STORAGE_KEY);
  if (raw === null) {
    return null;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    removeRaw(USER_STORAGE_KEY);
    return null;
  }
  if (!isUser(parsed)) {
    removeRaw(USER_STORAGE_KEY);
    return null;
  }
  return parsed;
}

function cacheUser(user: User | null): void {
  if (user === null) {
    removeRaw(USER_STORAGE_KEY);
    return;
  }
  writeRaw(USER_STORAGE_KEY, JSON.stringify(user));
}

class AuthStore {
  token = $state<string | null>(null);
  user = $state<User | null>(null);
  status = $state<AuthStatus>("idle");

  /** 会话代数：clear()/setSession() 自增，用于丢弃迟到的 me 结果（§9 最后一行）。 */
  private epoch = 0;
  /** 并发 bootstrap 共享的 in-flight Promise（§5、§9）。 */
  private inFlight: Promise<void> | null = null;

  private readonly onStorage = (): void => {
    const next = normalizeToken(readRaw(TOKEN_STORAGE_KEY));

    if (next === null) {
      const hadSession = this.token !== null;
      this.clear();
      if (hadSession) {
        // 另一标签页已登出：本标签页一并回登录页（replace，防后退）。
        navigate("/login", { replace: true });
      }
      return;
    }

    if (next === this.token) {
      // 只是 user 缓存变化：忽略，身份以回源结果为准（§8）。
      return;
    }

    // 另一标签页换了 token：同步后重新回源（§8）。
    this.token = next;
    this.user = readUserCache();
    this.status = "loading";
    void this.bootstrap();
  };

  constructor() {
    const storedToken = normalizeToken(readRaw(TOKEN_STORAGE_KEY));
    if (storedToken === null) {
      // 脏值（"null" / "undefined" / 空白）归一为未登录并删键（§3 规则 2）。
      removeRaw(TOKEN_STORAGE_KEY);
      removeRaw(USER_STORAGE_KEY);
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

  /** 只用于界面显隐与路由分流；权限以后端为准（auth.md §4、03 §五）。 */
  get role(): Role | null {
    return this.user?.role ?? null;
  }

  snapshot(): AuthSnapshot {
    return { status: this.status, role: this.role };
  }

  /** 登录成功写入会话：先 token、后 user（§6）；user 可空，交给 bootstrap 回源补齐。 */
  setSession(token: string, user?: User | null): void {
    const normalized = normalizeToken(token);
    if (normalized === null) {
      this.clear();
      return;
    }

    this.epoch += 1;
    writeRaw(TOKEN_STORAGE_KEY, normalized);
    cacheUser(user ?? null);
    this.token = normalized;
    this.user = user ?? null;
    this.status = "authed";
  }

  /** 登出/失效：先 user 后 token、removeItem、幂等、不发请求（§6）。 */
  clear(): void {
    this.epoch += 1;
    removeRaw(USER_STORAGE_KEY);
    removeRaw(TOKEN_STORAGE_KEY);
    this.token = null;
    this.user = null;
    this.status = "guest";
  }

  /** 启动回源：有 token 必请求 me；网络失败保留 token 不跳转（§4、§5）。 */
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

  /** 登录：成功后写会话，失败原样抛出（401 白名单由 client 负责，store 不重复判断）。 */
  async login(payload: LoginPayload): Promise<void> {
    if (authApi === null) {
      throw new ApiError(0, "请求客户端尚未接入（S2-13）");
    }

    const epoch = this.epoch;
    this.status = "loading";
    try {
      const result = await authApi.login(payload);
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

  /** 主动登出：先清后跳，避免守卫读到旧 token（§6、§10）。 */
  logout(): void {
    this.clear();
    navigate("/login", { replace: true });
  }

  private async runBootstrap(): Promise<void> {
    if (this.token === null) {
      // 无 token 不请求 me（§5）。
      this.status = "guest";
      return;
    }

    if (authApi === null) {
      // S2-13 之前没有请求客户端：保留 token，按未登录处理，只提示一次。
      warnOnce("[auth] 请求客户端尚未接入（S2-13），已有令牌但无法回源 me");
      this.status = "guest";
      return;
    }

    const epoch = this.epoch;
    this.status = "loading";

    try {
      const user = await authApi.me();
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
        // 令牌失效：清两键（§5、§7.4）。
        this.clear();
        return;
      }
      // 网络失败 / 信封异常 / 其它业务码：保留 token，不跳转（§5、§9）。
      this.status = "guest";
    }
  }
}

export const auth: AuthStore = new AuthStore();
