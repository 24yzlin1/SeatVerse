/** 页面仍然静态导入；组件依赖仅进入渲染层，不进入路由状态与公共出口。 */
import type { Component } from "svelte";
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

export const routeComponents: Readonly<Partial<Record<string, Component>>> = {
  login: LoginPage,
  register: RegisterPage,
  events: EventsPage,
  eventDetail: EventDetailPage,
  seatMap: SeatMapPage,
  bookings: BookingsPage,
  ticket: TicketPage,
  ticketByCode: TicketByCodePage,
  organizerEvents: OrganizerEventsPage,
  organizerBookings: OrganizerBookingsPage,
  verify: VerifyPage,
};
