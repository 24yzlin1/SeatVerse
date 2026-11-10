/**
 * 自写 hash 路由（零依赖）。
 *
 * 依据 docs/contracts/frontend-arch.md §1—§3 与 08 号计划 §8.1 的七条实现约束：
 *   1. 单例 + 模块级 `$state`，不用 context；
 *   2. 同时监听 `hashchange` 与 `popstate`，`init()` 先手动解析一次；
 *   3. 空 hash、`#`、`#/` 归一为 `/`，去掉末尾多余斜杠；
 *   4. 匹配优先级：静态段 > 动态段 > `*`，再按段数从多到少；
 *   5. 守卫顺序：redirect → requiresAuth → roles，未登录跳 `#/login?next=...`（replace）；
 *   6. `navigate` 用 `location.hash`；`replace` 走 `history.replaceState` 后手动解析一次；
 *   7. 同一路径重复 `navigate` 直接 return。
 *
 * 身份来源做成接缝：本步（S2-09）默认 guest，S2-12 的 auth store 落地后调用
 * `setAuthSource` 一次即可接上，路由逻辑不需要再改。
 */
import type { AuthSnapshot, AuthStatus } from "@/common/stores/auth.svelte";
import { HOME_BY_ROLE, routes } from "./routes";
import type { RouteDef } from "./routes";

// 会话类型唯一定义在 auth store（S2-12），这里只转出，避免两处漂移。
export type { AuthSnapshot, AuthStatus };

export interface AuthSource {
  /** 当前身份快照；必须是同步读取。 */
  snapshot: () => AuthSnapshot;
  /** `status === "idle"` 时守卫会先 await 它（frontend-arch.md §3.2）。 */
  bootstrap?: () => Promise<void>;
}

export interface NavigateOptions {
  /** 用 replaceState 改地址，不新增历史记录。 */
  replace?: boolean;
  /** 仅在目标为 `/login` 时作为 `next` 查询参数附加。 */
  next?: string;
}

interface MatchResult {
  route: RouteDef;
  params: Record<string, string>;
}

/** 默认身份：未登录。S2-12 会用真实 store 覆盖它。 */
const GUEST_SNAPSHOT: AuthSnapshot = { status: "guest", role: null };

let authSource: AuthSource = { snapshot: () => GUEST_SNAPSHOT };

export function setAuthSource(source: AuthSource): void {
  authSource = source;
}

/** `"/"` → `[]`；`"/events/9"` → `["events", "9"]`。保留空段以便识别 `#/events//seats`。 */
function splitSegments(path: string): string[] {
  if (path === "/") {
    return [];
  }
  return path.replace(/^\//, "").split("/");
}

/** 归一化 hash：`""`、`#`、`#/` 都视为 `/`，去掉末尾多余斜杠，查询串原样保留。 */
function normalizeHash(rawHash: string): { path: string; query: URLSearchParams } {
  const hash = rawHash.startsWith("#") ? rawHash.slice(1) : rawHash;
  const queryIndex = hash.indexOf("?");
  const rawPath = queryIndex >= 0 ? hash.slice(0, queryIndex) : hash;
  const rawQuery = queryIndex >= 0 ? hash.slice(queryIndex + 1) : "";

  let path = rawPath;
  if (path.length === 0) {
    path = "/";
  }
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }
  while (path.length > 1 && path.endsWith("/")) {
    path = path.slice(0, -1);
  }

  return { path, query: new URLSearchParams(rawQuery) };
}

function countStaticSegments(path: string): number {
  return splitSegments(path).filter((segment) => !segment.startsWith(":")).length;
}

/** 静态段优先，其次段数从多到少（frontend-arch.md §3.1）。 */
const orderedRoutes: RouteDef[] = [...routes]
  .filter((route) => route.path !== "*")
  .sort((left, right) => {
    const staticDelta = countStaticSegments(right.path) - countStaticSegments(left.path);
    if (staticDelta !== 0) {
      return staticDelta;
    }
    return splitSegments(right.path).length - splitSegments(left.path).length;
  });

const fallbackRoute: RouteDef | undefined = routes.find((route) => route.path === "*");

/** 逐段匹配；动态段必须非空，且解码失败视为不匹配。 */
function matchRoute(path: string): MatchResult | null {
  const segments = splitSegments(path);

  for (const route of orderedRoutes) {
    const pattern = splitSegments(route.path);
    if (pattern.length !== segments.length) {
      continue;
    }

    const params: Record<string, string> = {};
    let matched = true;

    for (let index = 0; index < pattern.length; index += 1) {
      const part = pattern[index];
      const actual = segments[index];

      if (part.startsWith(":")) {
        if (actual.length === 0) {
          matched = false;
          break;
        }
        try {
          params[part.slice(1)] = decodeURIComponent(actual);
        } catch {
          // 非法转义（如 `%E0%A4%A`）不匹配，交给 404，不能让页面白屏。
          matched = false;
          break;
        }
        continue;
      }

      if (part !== actual) {
        matched = false;
        break;
      }
    }

    if (matched) {
      return { route, params };
    }
  }

  return null;
}

class Router {
  /** 归一化后的当前路径，如 `/events/9/seats`。 */
  path = $state("/");
  /** 当前 hash 的查询串。 */
  query = $state.raw(new URLSearchParams());
  /** 动态段，值已 `decodeURIComponent`。 */
  params = $state.raw<Record<string, string>>({});
  /** 命中的路由；`init()` 之前为 null。 */
  matched = $state.raw<RouteDef | null>(null);
  /** 是否落到 `*` 兜底。 */
  isNotFound = $state(false);
  /** `init()` 是否已执行，RouteView 用它避免首帧闪 404。 */
  initialized = $state(false);

  private lastTarget = "";
  private guardToken = 0;
  private listening = false;

  private readonly onRouteChange = (): void => {
    this.apply();
  };

  init(): void {
    if (this.listening) {
      this.lastTarget = "";
      this.apply();
      return;
    }

    window.addEventListener("hashchange", this.onRouteChange);
    window.addEventListener("popstate", this.onRouteChange);
    this.listening = true;
    this.initialized = true;
    this.lastTarget = "";
    this.apply();
  }

  destroy(): void {
    window.removeEventListener("hashchange", this.onRouteChange);
    window.removeEventListener("popstate", this.onRouteChange);
    this.listening = false;
    // 作废在途守卫，避免 destroy 之后仍然跳转。
    this.guardToken += 1;
  }

  navigate(to: string, options: NavigateOptions = {}): void {
    let target = to;

    if (options.next !== undefined && target.startsWith("/login")) {
      const parsed = normalizeHash(`#${target}`);
      parsed.query.set("next", options.next);
      target = `${parsed.path}?${parsed.query.toString()}`;
    }

    if (!target.startsWith("/")) {
      target = `/${target}`;
    }

    if (target === this.readTarget()) {
      return;
    }

    if (options.replace === true) {
      history.replaceState(null, "", `#${target}`);
      // replaceState 不触发 hashchange，必须手动解析一次。
      this.lastTarget = "";
      this.apply();
      return;
    }

    location.hash = `#${target}`;
  }

  /** 读当前地址并归一化成可比较的目标串 `path?query`。 */
  private readTarget(): string {
    const { path, query } = normalizeHash(location.hash);
    const queryString = query.toString();
    if (queryString.length === 0) {
      return path;
    }
    return `${path}?${queryString}`;
  }

  /** 解析当前地址、匹配路由、写状态、跑守卫。同一目标重复调用直接返回。 */
  private apply(): void {
    const target = this.readTarget();
    if (target === this.lastTarget) {
      return;
    }
    this.lastTarget = target;

    const { path, query } = normalizeHash(location.hash);
    const result = matchRoute(path);
    const route = result?.route ?? fallbackRoute ?? null;

    this.path = path;
    this.query = query;
    this.params = result?.params ?? {};
    this.matched = route;
    this.isNotFound = route === null || route.path === "*";

    this.guardToken += 1;
    void this.runGuards(route, target, this.guardToken);
  }

  private async runGuards(
    route: RouteDef | null,
    target: string,
    token: number,
  ): Promise<void> {
    if (route === null) {
      return;
    }

    if (route.redirect !== undefined) {
      if (token !== this.guardToken) {
        return;
      }
      this.navigate(route.redirect, { replace: true });
      return;
    }

    const snapshot = await this.readAuth();
    if (token !== this.guardToken) {
      return;
    }

    if (route.requiresAuth === true && snapshot.status !== "authed") {
      const next = encodeURIComponent(target);
      this.navigate(`/login?next=${next}`, { replace: true });
      return;
    }

    if (route.roles !== undefined && route.roles.length > 0) {
      const role = snapshot.role;
      if (role === null) {
        this.navigate(HOME_BY_ROLE.user, { replace: true });
        return;
      }
      if (!route.roles.includes(role)) {
        this.navigate(HOME_BY_ROLE[role], { replace: true });
      }
    }
  }

  /** 读身份；`idle` 且提供了 bootstrap 时先启动一次（auth.md §5 的网络失败不清令牌）。 */
  private async readAuth(): Promise<AuthSnapshot> {
    const snapshot = authSource.snapshot();
    if (snapshot.status !== "idle" || authSource.bootstrap === undefined) {
      return snapshot;
    }

    try {
      await authSource.bootstrap();
    } catch {
      // 网络失败：不改变身份判断，保持调用前的快照。
      return snapshot;
    }

    return authSource.snapshot();
  }
}

export const router: Router = new Router();

export function navigate(to: string, options: NavigateOptions = {}): void {
  router.navigate(to, options);
}
