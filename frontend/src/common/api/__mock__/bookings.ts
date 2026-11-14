/**
 * 临时 mock：真实 `GET /bookings/me` 上线后删除本文件，
 * 并把预约列表的数据源切回真实请求。
 *
 * 假数据只允许出现在本文件，禁止散落到页面组件。
 * 字段与 `docs/contracts/api.md` §4.1、`samples/bookings-me.ok.json` 保持一致。
 */
import type { Booking, Page } from "@/common/api/types";

const MOCK_BOOKINGS: Booking[] = [
  {
    id: 9001,
    status: "reserved",
    createdAt: "2026-11-06T19:30:00+08:00",
    cancelledAt: null,
    ticketCode: "SV7F3K9Q2M4T8X6B5N2P",
    event: {
      id: 12,
      title: "校园技术分享会：从零构建 3D 选座",
      status: "published",
      startTime: "2026-11-20T19:00:00+08:00",
      endTime: "2026-11-20T21:00:00+08:00",
      venue: { id: 1, name: "学生活动中心·主报告厅" },
    },
    seats: [
      { id: 308, row: 3, number: 12, label: "3排12号", seatType: "standard" },
      { id: 309, row: 3, number: 13, label: "3排13号", seatType: "standard" },
    ],
  },
  {
    id: 9002,
    status: "reserved",
    createdAt: "2026-11-02T10:00:00+08:00",
    cancelledAt: null,
    ticketCode: "SV3N8R6T2W9Y4K7J5M1C",
    event: {
      id: 11,
      title: "校园音乐夜",
      status: "published",
      startTime: "2026-11-10T19:00:00+08:00",
      endTime: "2026-11-10T21:00:00+08:00",
      venue: { id: 1, name: "学生活动中心·主报告厅" },
    },
    seats: [
      { id: 412, row: 5, number: 8, label: "5排8号", seatType: "standard" },
    ],
  },
  {
    id: 9003,
    status: "cancelled",
    createdAt: "2026-11-01T09:12:00+08:00",
    cancelledAt: "2026-11-05T10:05:00+08:00",
    ticketCode: "SV9Q4W7E2R5T8Y3A6B1C",
    event: {
      id: 13,
      title: "社团开放日：秋季招新",
      status: "closed",
      startTime: "2026-11-18T19:00:00+08:00",
      endTime: "2026-11-18T21:00:00+08:00",
      venue: { id: 1, name: "学生活动中心·主报告厅" },
    },
    seats: [
      { id: 101, row: 2, number: 4, label: "2排4号", seatType: "standard" },
    ],
  },
  {
    id: 9004,
    status: "used",
    createdAt: "2026-10-28T12:00:00+08:00",
    cancelledAt: null,
    ticketCode: "SV2M5N8B3V6C9X4Z7A1S",
    event: {
      id: 14,
      title: "期末备考讲座",
      status: "published",
      startTime: "2026-11-12T14:00:00+08:00",
      endTime: "2026-11-12T16:00:00+08:00",
      venue: { id: 1, name: "学生活动中心·主报告厅" },
    },
    seats: [
      { id: 260, row: 8, number: 10, label: "8排10号", seatType: "standard" },
    ],
  },
];

/** “我的预约”列表的 mock 分页结构；返回深拷贝，调用方修改不会污染常量。 */
export function mockBookingsPage(): Page<Booking> {
  return {
    items: structuredClone(MOCK_BOOKINGS),
    total: MOCK_BOOKINGS.length,
    page: 1,
    pageSize: 20,
  };
}
