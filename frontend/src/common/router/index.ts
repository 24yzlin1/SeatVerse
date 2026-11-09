/**
 * 路由层统一出口。
 *
 * 页面与组件只从这里导入，不直接引用 `router.svelte.ts` 或 `routes.ts` 的相对路径，
 * 便于后续把内部实现（如 S2-12 的 auth 接缝）替换掉而不影响调用方。
 */
export { navigate, router, setAuthSource } from "./router.svelte";
export { HOME_BY_ROLE, routes } from "./routes";
export type {
  AuthSnapshot,
  AuthSource,
  AuthStatus,
  NavigateOptions,
} from "./router.svelte";
export type { Role, RouteDef } from "./routes";
