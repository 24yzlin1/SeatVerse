/**
 * 我的预约数据加载。
 *
 * 真实接口 `GET /bookings/me` 尚未就绪，当前返回本地演示数据；
 * 接口上线后把 USE_MOCK_BOOKINGS 改为 false，并删除 `__mock__` 目录。
 */
import { endpoints, request } from "@/common/api";
import { mockBookingsPage } from "@/common/api/__mock__/bookings";
import type { Booking, Page } from "@/common/api/types";

/** 临时开关：演示数据与真实接口之间切换。 */
export const USE_MOCK_BOOKINGS = true;

/** 读取“我的预约”列表；当前只取第 1 页。 */
export async function loadBookings(): Promise<Page<Booking>> {
  if (USE_MOCK_BOOKINGS) {
    return mockBookingsPage();
  }
  return request<Page<Booking>>(endpoints.bookingsMe());
}
