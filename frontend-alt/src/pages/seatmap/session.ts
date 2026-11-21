import { ApiError } from "@/common/api/types";
import type { Booking } from "@/common/api";
import { bookingBlockReason } from "./data";
import {
  clearSelection,
  filterSelection,
  toggleSeatSelection,
} from "./selection";
import type { EventId, SeatId, SeatMapData, SelectedSeatIds } from "./types";

/** 真实接口与本地演示使用同一流程；正式页面只注入真实 API。 */
export interface SeatMapApi {
  loadSeatMap: (id: EventId, signal?: AbortSignal) => Promise<SeatMapData>;
  submitBooking: (id: EventId, seats: readonly SeatId[]) => Promise<Booking>;
}

export interface SeatMapState {
  readonly pageState: "loading" | "error" | "ready";
  readonly data: SeatMapData | null;
  readonly selected: SelectedSeatIds;
  readonly loadingError: string;
  readonly refreshError: string;
  readonly refreshing: boolean;
  readonly submitting: boolean;
  readonly notice: string;
  readonly feedback: string;
  readonly completed: Booking | null;
}

function initialState(): SeatMapState {
  return {
    pageState: "loading",
    data: null,
    selected: clearSelection(),
    loadingError: "",
    refreshError: "",
    refreshing: false,
    submitting: false,
    notice: "",
    feedback: "请选择座位",
    completed: null,
  };
}

function message(error: unknown): string {
  if (error instanceof ApiError && error.code === 404) {
    return "活动或场馆不存在，请返回活动列表重新选择";
  }
  return error instanceof Error ? error.message : "服务暂时不可用，请稍后重试";
}

export function seatMapBlockReason(
  state: SeatMapState,
  now = Date.now(),
): string {
  if (state.refreshing) {
    return "正在更新座位状态";
  }
  if (state.refreshError) {
    return "座位状态更新失败，请先刷新";
  }
  if (!state.data || state.pageState !== "ready") {
    return "正在加载活动与座位";
  }
  const { event, seats, seatStates } = state.data;
  const blocked = bookingBlockReason(event, now);
  if (blocked) {
    return blocked;
  }
  if (seats.length === 0) {
    return "场馆尚未配置座位";
  }
  if (
    seats.some(
      (seat) =>
        !["available", "sold", "locked"].includes(
          seatStates.get(seat.id) ?? "",
        ),
    )
  ) {
    return "座位状态不完整或异常，请刷新后重试";
  }
  if (seats.every((seat) => seatStates.get(seat.id) === "sold")) {
    return "本场座位已满，可稍后刷新或选择其他活动";
  }
  if (!seats.some((seat) => seatStates.get(seat.id) === "available")) {
    return "当前暂无可选座位，请稍后刷新";
  }
  return "";
}

/** 每次活动切换独立计代，刷新另计版本；abort 仅用于节约请求。 */
export class SeatMapSession {
  private value = initialState();
  private eventId = Number.NaN;
  private context = 0;
  private requestVersion = 0;
  private controller: AbortController | null = null;

  constructor(
    private readonly api: SeatMapApi,
    private readonly onChange: (state: SeatMapState) => void = () => {},
  ) {}

  get state(): SeatMapState {
    return this.value;
  }

  private update(patch: Partial<SeatMapState>): void {
    this.value = { ...this.value, ...patch };
    this.onChange(this.value);
  }

  disabledReason(now = Date.now()): string {
    return seatMapBlockReason(this.value, now);
  }

  async open(id: EventId): Promise<void> {
    this.dispose();
    this.eventId = id;
    this.update(initialState());
    await this.load(true);
  }

  dispose(): void {
    this.context++;
    this.requestVersion++;
    this.controller?.abort();
  }

  async refresh(): Promise<void> {
    if (this.value.submitting) {
      return;
    }
    await this.load(false);
  }

  private async load(
    initial: boolean,
    id = this.eventId,
    scope = this.context,
  ): Promise<void> {
    const version = ++this.requestVersion;
    this.controller?.abort();
    const controller = new AbortController();
    this.controller = controller;
    this.update({ refreshing: true, refreshError: "", loadingError: "" });
    try {
      const data = await this.api.loadSeatMap(id, controller.signal);
      if (scope !== this.context || version !== this.requestVersion) {
        return;
      }
      if (data.event.id !== id) {
        throw new Error("活动编号与当前页面不一致，请重新进入活动");
      }
      const selected = filterSelection(
        this.value.selected,
        data.seats,
        data.seatStates,
      );
      const feedback =
        selected.size < this.value.selected.size
          ? "部分选择已失效，已保留仍可预约的座位"
          : this.value.feedback;
      this.update({ data, selected, feedback, pageState: "ready" });
    } catch (error) {
      if (
        scope !== this.context ||
        version !== this.requestVersion ||
        controller.signal.aborted
      ) {
        return;
      }
      this.update(
        initial
          ? { loadingError: message(error), pageState: "error" }
          : { refreshError: message(error) },
      );
    } finally {
      if (scope === this.context && version === this.requestVersion) {
        this.update({ refreshing: false });
      }
    }
  }

  toggle(id: SeatId, now = Date.now()): void {
    const { data, selected, submitting, refreshing } = this.value;
    if (
      !data ||
      submitting ||
      refreshing ||
      (this.disabledReason(now) && !selected.has(id))
    ) {
      return;
    }
    const seat = data.seats.find((seat) => seat.id === id);
    if (!seat || data.seatStates.get(id) !== "available") {
      return;
    }
    this.update({
      selected: toggleSeatSelection(selected, id, data.seats, data.seatStates),
      feedback: `${seat.label}${selected.has(id) ? "已取消选择" : "已选中"}`,
      notice: "",
      completed: null,
    });
  }

  clear(): void {
    if (this.value.submitting || this.value.refreshing) {
      return;
    }
    this.update({
      selected: clearSelection(),
      feedback: "已清空选择",
      notice: "",
    });
  }

  async confirm(now = Date.now()): Promise<void> {
    const { data, selected, submitting } = this.value;
    if (
      !data ||
      submitting ||
      this.disabledReason(now) ||
      selected.size === 0
    ) {
      return;
    }
    const id = data.event.id;
    const scope = this.context;
    const seatIds = Object.freeze([...selected].sort((a, b) => a - b));
    this.update({ submitting: true, notice: "", completed: null });
    try {
      const completed = await this.api.submitBooking(id, seatIds);
      if (scope !== this.context) {
        return;
      }
      this.update({
        completed,
        selected: clearSelection(),
        feedback: "预约成功，座位已更新",
        submitting: false,
      });
      await this.load(false, id, scope);
    } catch (error) {
      if (scope !== this.context) {
        return;
      }
      const uncertain =
        error instanceof ApiError && (error.code <= 0 || error.code >= 500);
      this.update({
        notice: uncertain
          ? "提交结果未能确认，请先查看我的预约，避免重复预约；座位状态将重新核对。"
          : error instanceof ApiError && error.code === 409
            ? `${message(error)}；请在状态更新后确认剩余选择或重新选座。`
            : message(error),
      });
      // POST 不自动重试；业务拒绝和传输失败均先回源，401 交给公共客户端。
      if (!(error instanceof ApiError && error.code === 401)) {
        await this.load(false, id, scope);
      }
    } finally {
      if (scope === this.context) {
        this.update({ submitting: false });
      }
    }
  }
}
