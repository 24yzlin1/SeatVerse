/**
 * 接口类型定义。
 *
 * 字段一律照契约与样例逐字写，不凭印象：
 *   - 信封与分页：docs/contracts/api.md §2
 *   - 预约与电子票：api.md §4.1、§4.3
 *   - 登录与用户：docs/contracts/auth.md §14.2
 *   - 角色与状态字面量：docs/contracts/enums.md §2.1、§2.2、§2.4、§2.5、§2.6
 *   - 样例对照：docs/contracts/samples/*.json
 *
 * 时间字段统一为 ISO 8601 带时区偏移的字符串（样例为 `+08:00`），前端只做展示，不做时区换算。
 */

// ===== 角色与状态枚举（enums.md） =====

/** 角色字面量；只用于界面显隐，权限以后端为准（03 §五）。 */
export type Role = "user" | "organizer";

/** 预约状态（enums.md §2.4）；“已完成 / 进行中 / 已结束”是派生展示态，不在此列。 */
export type BookingStatus = "reserved" | "cancelled" | "used";

/** 电子票状态（enums.md §2.5）：由预约状态与核验结果派生，与预约同字面量、不同语义。 */
export type TicketStatus = "reserved" | "cancelled" | "used";

/** 活动状态（enums.md §2.2）；“进行中 / 已结束”按时间派生，不写库。 */
export type EventStatus = "draft" | "published" | "closed" | "cancelled";

/** 座位类型（enums.md §2.6）：第一版只有普通座。 */
export type SeatType = "standard";

// ===== 实体（api.md §4.1 / §4.3 / auth.md §14.2） =====

export interface VenueBrief {
  id: number;
  name: string;
}

export interface EventSummary {
  id: number;
  title: string;
  status: EventStatus;
  /** ISO 8601 */
  startTime: string;
  /** ISO 8601，必须晚于 startTime */
  endTime: string;
  venue: VenueBrief;
}

export interface SeatBrief {
  id: number;
  /** 排号，>= 1 */
  row: number;
  /** 座号，>= 1 */
  number: number;
  /** 展示名，固定 `{row}排{number}号` */
  label: string;
  seatType: SeatType;
}

/** `GET /authentication/me` 的 payload 就是该对象本身，不再包一层 `{ user }`（auth.md §14.2 约束 4）。 */
export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
}

/** 登录与注册的成功 payload（auth.md §14.2）。 */
export interface LoginResponse {
  token: string;
  user: User;
}

/**
 * 登录请求体。
 *
 * 契约只冻结了响应（auth.md §14.2），请求字段以 D 的实现 `LoginRequest` 为准：
 * `{ email, password }`（backend/app/types/authentication.py）。
 */
export interface LoginPayload {
  email: string;
  password: string;
}

export interface Booking {
  id: number;
  status: BookingStatus;
  /** ISO 8601 */
  createdAt: string;
  /** 未取消为 null；cancelled 时非空 */
  cancelledAt: string | null;
  /** 内联票号，20 位，规则见 docs/contracts/ticket-qr.md */
  ticketCode: string;
  event: EventSummary;
  /** 至少 1 个，按 row、number 升序 */
  seats: SeatBrief[];
}

export interface Ticket {
  id: number;
  bookingId: number;
  ticketCode: string;
  status: TicketStatus;
  /** 出票时间，等于对应预约的 createdAt（同一事务生成，不单独存储） */
  issuedAt: string;
  /** 未核验为 null */
  verifiedAt: string | null;
  /** 核验人用户编号；未核验为 null */
  verifiedBy: number | null;
  event: EventSummary;
  seats: SeatBrief[];
}

// ===== 信封与分页（api.md §2） =====

/** 统一响应信封：HTTP 恒 200，成败只看 `code === 200`。 */
export interface Envelope<T> {
  code: number;
  /** 可直接展示的中文提示 */
  message: string;
  /** 失败时通常为 null */
  payload: T | null;
}

/** 列表统一信封内的分页结构；page 从 1 开始。 */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// ===== 异常 =====

/**
 * 请求层的统一异常。
 *
 * code 取值（08 §8.2 的分支顺序）：
 *   0  传输失败 / 超时
 *   -1 响应不是统一信封（解析失败、缺 code/message）
 *   其余为后端业务码 400 / 401 / 403 / 404 / 409
 */
export class ApiError extends Error {
  readonly code: number;

  constructor(code: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}
