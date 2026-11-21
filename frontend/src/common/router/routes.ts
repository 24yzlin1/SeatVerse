/**
 * 路由表与路由类型。
 *
 * 依据 docs/contracts/frontend-arch.md §3.4（13 条路由）与 §1（自写 hash 路由、零依赖）。
 * 路由路径一律写成归一化形式：不带 `#`、不带末尾斜杠、动态段用 `:name`。
 * 此文件只定义元数据，不导入页面；静态组件表由 RouteView 单独加载，避免反向循环。
 */
import type { Role } from "@/common/api/types";

/** 角色字面量与 docs/contracts/enums.md §2.1 一致；唯一定义在 `@/common/api/types`，此处转出以便路由层自洽。 */
export type { Role };

export interface RouteDef {
  /** 路由名，仅用于调试与 404 判定，不参与匹配。 */
  name: string;
  /** 归一化路径；`*` 为兜底。 */
  path: string;
  /** 需要登录才能访问（frontend-arch.md §3.2）。 */
  requiresAuth?: boolean;
  /** 需要的角色；为空表示不限角色。 */
  roles?: Role[];
  /** 命中后直接改写到该路径，使用 replace。 */
  redirect?: string;
}

/** 登录成功、角色不符时的回退落点（frontend-arch.md §3.2）。 */
export const HOME_BY_ROLE: Record<Role, string> = {
  user: "/events",
  organizer: "/organizer/events",
};

/**
 * 13 条路由。匹配优先级由 router 按「静态段优先、段数从多到少」排序决定，
 * 此处顺序只影响可读性，不影响匹配结果。
 */
export const routes: RouteDef[] = [
  { name: "index", path: "/", redirect: "/events" },
  { name: "login", path: "/login" },
  { name: "register", path: "/register" },
  { name: "events", path: "/events" },
  { name: "eventDetail", path: "/events/:id" },
  { name: "seatMap", path: "/events/:id/seats" },
  { name: "bookings", path: "/bookings", requiresAuth: true },
  {
    name: "ticket",
    path: "/bookings/:id/ticket",
    requiresAuth: true,
  },
  {
    name: "ticketByCode",
    path: "/tickets/:code",
    requiresAuth: true,
  },
  {
    name: "organizerEvents",
    path: "/organizer/events",
    requiresAuth: true,
    roles: ["organizer"],
  },
  {
    name: "organizerBookings",
    path: "/organizer/events/:id/bookings",
    requiresAuth: true,
    roles: ["organizer"],
  },
  {
    name: "verify",
    path: "/organizer/verify",
    requiresAuth: true,
    roles: ["organizer"],
  },
  // 兜底路由不带组件：404 页需要拿到失败路径，由 RouteView 直接渲染 <NotFound path={...} />。
  { name: "notFound", path: "*" },
];
