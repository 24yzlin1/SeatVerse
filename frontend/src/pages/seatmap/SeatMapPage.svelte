<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { navigate, router } from "@/common/router";
  import { auth } from "@/common/stores/auth.svelte";
  import { ApiError } from "@/common/api";
  import type { Booking } from "@/common/api";
  import Loading from "@/common/components/Loading.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import SeatSelectionPage from "./SeatSelectionPage.svelte";
  import { loadSeatMap, submitBooking } from "./api";
  import { bookingBlockReason } from "./data";
  import {
    clearSelection,
    filterSelection,
    toggleSeatSelection,
  } from "./selection";
  import type { SeatId, SeatMapData, SelectedSeatIds } from "./types";

  const rawId = $derived(router.params.id ?? "");
  const eventId = $derived(
    /^[1-9]\d*$/.test(rawId) && Number.isSafeInteger(Number(rawId))
      ? Number(rawId)
      : Number.NaN,
  );
  let pageState = $state<"loading" | "error" | "ready">("loading");
  let data = $state.raw<SeatMapData | null>(null);
  let selected = $state.raw<SelectedSeatIds>(clearSelection());
  let loadingError = $state("");
  let refreshError = $state("");
  let refreshing = $state(false);
  let submitting = $state(false);
  let notice = $state("");
  let feedback = $state("请选择座位");
  let completed = $state.raw<Booking | null>(null);
  let now = $state(Date.now());
  let context = 0;
  let requestVersion = 0;
  let loadController: AbortController | null = null;

  const blocked = $derived(
    data ? bookingBlockReason(data.event, now) : "正在加载活动",
  );
  const disabledReason = $derived(
    refreshing
      ? "正在更新座位状态"
      : refreshError
        ? "座位状态更新失败，请先刷新"
        : blocked || (data?.seats.length === 0 ? "场馆尚未配置座位" : ""),
  );
  const selectionDisabled = $derived(
    submitting || Boolean(disabledReason) || pageState !== "ready",
  );

  function message(error: unknown): string {
    return error instanceof Error
      ? error.message
      : "服务暂时不可用，请稍后重试";
  }

  async function refresh(
    initial = false,
    id = eventId,
    scope = context,
  ): Promise<void> {
    const version = ++requestVersion;
    loadController?.abort();
    const controller = new AbortController();
    loadController = controller;
    if (initial) {
      pageState = "loading";
      data = null;
      selected = clearSelection();
      submitting = false;
      completed = null;
      notice = "";
      feedback = "请选择座位";
    }
    refreshing = true;
    refreshError = "";
    loadingError = "";
    try {
      const result = await loadSeatMap(id, controller.signal);
      if (scope !== context || version !== requestVersion) return;
      const valid = filterSelection(selected, result.seats, result.seatStates);
      if (valid.size < selected.size)
        feedback = "部分选择已失效，已保留仍可预约的座位";
      selected = valid;
      data = result;
      pageState = "ready";
    } catch (error) {
      if (
        scope !== context ||
        version !== requestVersion ||
        controller.signal.aborted
      )
        return;
      if (initial) {
        loadingError = message(error);
        pageState = "error";
      } else {
        refreshError = message(error);
      }
    } finally {
      if (scope === context && version === requestVersion) refreshing = false;
    }
  }

  function toggleSeat(id: SeatId) {
    if (
      !data ||
      submitting ||
      refreshing ||
      (selectionDisabled && !selected.has(id))
    )
      return;
    const seat = data.seats.find((seat) => seat.id === id);
    if (!seat || data.seatStates.get(id) !== "available") return;
    const wasSelected = selected.has(id);
    selected = toggleSeatSelection(selected, id, data.seats, data.seatStates);
    feedback = `${seat.label}${wasSelected ? "已取消选择" : "已选中"}`;
    notice = "";
  }

  function clearSeats() {
    if (submitting) return;
    selected = clearSelection();
    feedback = "已清空选择";
  }

  async function confirmSeats() {
    if (!auth.isLoggedIn) {
      navigate(`/login?next=${encodeURIComponent(`/events/${eventId}/seats`)}`);
      return;
    }
    if (!data || submitting || disabledReason || selected.size === 0) return;
    const id = data.event.id;
    const scope = context;
    const seatIds = [...selected].sort((a, b) => a - b);
    submitting = true;
    notice = "";
    completed = null;
    try {
      const result = await submitBooking(id, seatIds);
      if (scope !== context) return;
      completed = result;
      selected = clearSelection();
      feedback = "预约成功，座位已更新";
      await refresh(false, id, scope);
    } catch (error) {
      if (scope !== context) return;
      notice =
        error instanceof ApiError && error.code === 0
          ? "提交结果未能确认，请先查看我的预约；座位状态将重新核对。"
          : message(error);
      // POST 不自动重试。冲突、活动关闭和传输失败均先回源确认状态。
      if (!(error instanceof ApiError && error.code === 401))
        await refresh(false, id, scope);
    } finally {
      if (scope === context) submitting = false;
    }
  }

  $effect(() => {
    const id = eventId;
    const scope = ++context;
    untrack(() => {
      void refresh(true, id, scope);
    });
    return () => {
      context++;
      requestVersion++;
      loadController?.abort();
    };
  });

  onMount(() => {
    const update = () => {
      now = Date.now();
      if (
        document.visibilityState === "visible" &&
        pageState === "ready" &&
        !refreshing &&
        !submitting
      )
        void refresh();
    };
    const clock = window.setInterval(() => {
      now = Date.now();
    }, 1000);
    const poll = window.setInterval(update, 30000);
    window.addEventListener("focus", update);
    document.addEventListener("visibilitychange", update);
    return () => {
      clearInterval(clock);
      clearInterval(poll);
      window.removeEventListener("focus", update);
      document.removeEventListener("visibilitychange", update);
    };
  });
</script>

{#if pageState === "loading"}
  <section class="loading-page" aria-label="正在加载活动与座位">
    <Loading />
  </section>
{:else if pageState === "error"}
  <section class="loading-page">
    <ErrorState message={loadingError} />
    <div class="actions">
      <button type="button" onclick={() => refresh(true)}>重新加载</button><a
        href="#/events">返回活动列表</a
      >
    </div>
  </section>
{:else if data}
  <div class="notifications">
    {#if notice}<p class="alert" role="alert">
        {notice}
        {#if auth.isLoggedIn}<a href="#/bookings">查看我的预约</a>{/if}
      </p>{/if}
    {#if refreshError}<p class="alert" role="alert">
        {refreshError}，请刷新座位后继续。
      </p>{/if}
    {#if completed}
      <section class="success" role="status" aria-label="预约成功">
        <h2>预约成功</h2>
        <p>
          {completed.event.title} · {completed.seats
            .map((seat) => seat.label)
            .join("、")}
        </p>
        <p>
          预约编号：{completed.id} · 票号：<span class="ticket-code"
            >{completed.ticketCode}</span
          >
        </p>
        <a href="#/bookings">查看我的预约</a>
      </section>
    {/if}
  </div>
  <SeatSelectionPage
    {data}
    selectedSeatIds={selected}
    {submitting}
    {refreshing}
    {disabledReason}
    {selectionDisabled}
    {feedback}
    loggedIn={auth.isLoggedIn}
    onSeatToggle={toggleSeat}
    onClear={clearSeats}
    onSubmit={confirmSeats}
    onRefresh={() => refresh()}
  />
{/if}

<style>
  .loading-page {
    max-width: 1000px;
    margin: 48px auto;
    padding: 24px;
  }
  .actions {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
  }
  button {
    padding: 10px 18px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    cursor: pointer;
  }
  a {
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  .notifications {
    max-width: 1120px;
    margin: 0 auto;
    padding: 0 24px;
  }
  .alert,
  .success {
    margin-top: 20px;
    padding: 18px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    line-height: 1.8;
  }
  .alert {
    color: var(--destructive);
  }
  .success {
    border-color: var(--seat-available);
    background: var(--card);
  }
  .success h2 {
    font-size: 18px;
    font-weight: 650;
  }
  .ticket-code {
    overflow-wrap: anywhere;
    font-variant-numeric: tabular-nums;
  }
</style>
