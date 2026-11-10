/**
 * 接口路径常量。
 *
 * 依据 docs/contracts/api.md §3 的“路由内 path”列（**不含** `/api`）：
 * 前缀由请求客户端的 baseURL 负责（api.md §1），这里一旦写上 `/api` 就会变成双重前缀。
 *
 * 路径参数一律 `encodeURIComponent` 后拼接（api.md §3 约定第 1 条）；
 * 票号是 20 位 Crockford Base32（ticket-qr.md §2.1），仍然照编码规则处理，不假设字符集安全。
 */

/** 路径段编码；id 允许 number，调用方直接传 `booking.id` 即可。 */
const segment = (value: string | number): string => encodeURIComponent(String(value));

export const endpoints = {
  authLogin: () => "/authentication/login",
  authMe: () => "/authentication/me",
  bookingsMe: () => "/bookings/me",
  bookingCancel: (id: string | number) => `/bookings/${segment(id)}/cancel`,
  bookingTicket: (id: string | number) => `/bookings/${segment(id)}/ticket`,
  ticketByCode: (code: string) => `/tickets/${segment(code)}`,
} as const;
