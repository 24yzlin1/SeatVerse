import { ApiError, endpoints, request } from "@/common/api";
import type { Booking, Page } from "@/common/api";

/** 只读取真实接口；合并分页后再交给页面按状态分组。 */
export async function loadBookings(
  signal?: AbortSignal,
): Promise<{ items: Booking[]; total: number }> {
  const pageSize = 100;
  const first = await request<Page<Booking>>(
    `${endpoints.bookingsMe()}?page=1&pageSize=${pageSize}`,
    { signal },
  );
  if (
    !first ||
    !Array.isArray(first.items) ||
    !Number.isSafeInteger(first.total) ||
    first.total < 0
  )
    throw new ApiError(-1, "预约列表格式异常，请刷新后重试");
  const items = [...first.items];
  for (let page = 2; page <= Math.ceil(first.total / pageSize); page++) {
    const next = await request<Page<Booking>>(
      `${endpoints.bookingsMe()}?page=${page}&pageSize=${pageSize}`,
      { signal },
    );
    if (!next || !Array.isArray(next.items))
      throw new ApiError(-1, "预约列表格式异常，请刷新后重试");
    items.push(...next.items);
  }
  const unique = new Map(items.map((booking) => [booking.id, booking]));
  return { items: [...unique.values()], total: first.total };
}
