/**
 * 路由表与路由类型。
 *
 * 依据 docs/contracts/frontend-arch.md §3.4（13 条路由）与 §1（自写 hash 路由、零依赖）。
 * 路由路径一律写成归一化形式：不带 `#`、不带末尾斜杠、动态段用 `:name`。
 * 页面全部静态导入：契约 §1.4 明确不做路由级代码分割。
 */
import type { Component } from "svelte";

import type { Role } from "@/common/api/types";
import LoginPage from "@/pages/authentication/LoginPage.svelte";
import RegisterPage from "@/pages/authentication/RegisterPage.svelte";
import BookingsPage from "@/pages/bookings/BookingsPage.svelte";
import EventDetailPage from "@/pages/events/EventDetailPage.svelte";
import EventsPage from "@/pages/events/EventsPage.svelte";
import OrganizerBookingsPage from "@/pages/organizer/OrganizerBookingsPage.svelte";
import OrganizerEventsPage from "@/pages/organizer/OrganizerEventsPage.svelte";
import VerifyPage from "@/pages/organizer/VerifyPage.svelte";
import SeatMapPage from "@/pages/seatmap/SeatMapPage.svelte";
import TicketByCodePage from "@/pages/tickets/TicketByCodePage.svelte";
import TicketPage from "@/pages/tickets/TicketPage.svelte";

/** 角色字面量与 docs/contracts/enums.md §2.1 一致；唯一定义在 `@/common/api/types`，此处转出以便路由层自洽。 */
export type { Role };

export interface RouteDef {
  /** 路由名，仅用于调试与 404 判定，不参与匹配。 */
  name: string;
  /** 归一化路径；`*` 为兜底。 */
  path: string;
  /** 页面组件；带 `redirect` 的路由没有组件。 */
  component?: Component;
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
  { name: "login", path: "/login", component: LoginPage },
  { name: "register", path: "/register", component: RegisterPage },
  { name: "events", path: "/events", component: EventsPage },
  { name: "eventDetail", path: "/events/:id", component: EventDetailPage },
  { name: "seatMap", path: "/events/:id/seats", component: SeatMapPage },
  { name: "bookings", path: "/bookings", component: BookingsPage, requiresAuth: true },
  {
    name: "ticket",
    path: "/bookings/:id/ticket",
    component: TicketPage,
    requiresAuth: true,
  },
  {
    name: "ticketByCode",
    path: "/tickets/:code",
    component: TicketByCodePage,
    requiresAuth: true,
  },
  {
    name: "organizerEvents",
    path: "/organizer/events",
    component: OrganizerEventsPage,
    requiresAuth: true,
    roles: ["organizer"],
  },
  {
    name: "organizerBookings",
    path: "/organizer/events/:id/bookings",
    component: OrganizerBookingsPage,
    requiresAuth: true,
    roles: ["organizer"],
  },
  {
    name: "verify",
    path: "/organizer/verify",
    component: VerifyPage,
    requiresAuth: true,
    roles: ["organizer"],
  },
  // 兜底路由不带组件：404 页需要拿到失败路径，由 RouteView 直接渲染 <NotFound path={...} />。
  { name: "notFound", path: "*" },
];
