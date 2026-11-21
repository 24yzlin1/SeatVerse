<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { toast } from "svelte-sonner";

  import { authentication } from "@/common/stores/authentication.svelte";
  import SeatBookingSection from "@/pages/seatmap/components/SeatBookingSection.svelte";
  import { loadSeatMap, submitBooking } from "./api";
  import {
    clearSelection,
    filterSelection,
    toggleSeatSelection,
  } from "./selection";
  import type { SeatId, SeatMapData, SelectedSeatIds } from "./types";

  // Container for the seat booking flow. Mounted only while the "立即选座"
  // tab (or the seat map route) is active; `eventId` comes from the detail
  // page route. The flat plan and the 3D panorama share the same local
  // selection, so toggling the mode never loses chosen seats.
  const { eventId }: { eventId: number } = $props();

  let pageState = $state<"idle" | "loading" | "ready">("idle");
  let data = $state.raw<SeatMapData | null>(null);
  let selected = $state.raw<SelectedSeatIds>(clearSelection());
  let submitting = $state(false);
  let refreshing = $state(false);
  let requestVersion = 0;
  let loadController: AbortController | null = null;

  async function refresh(
    initial = false,
    targetEventId = eventId,
  ): Promise<void> {
    const version = ++requestVersion;
    loadController?.abort();
    const controller = new AbortController();
    loadController = controller;
    if (initial) {
      pageState = "loading";
      data = null;
      selected = clearSelection();
    }
    refreshing = true;
    try {
      const result = await loadSeatMap(targetEventId, controller.signal);
      if (version !== requestVersion || controller.signal.aborted) return;
      const valid = filterSelection(selected, result.seats, result.seatStates);
      if (valid.size < selected.size)
        toast.info("部分选择已失效，已保留仍可预约的座位");
      selected = valid;
      data = result;
      pageState = "ready";
    } catch (error: unknown) {
      if (version !== requestVersion || controller.signal.aborted) return;
      // Seat map failures are not fatal for the whole page; report via toast
      // and keep the tab empty so the user can retry by switching tabs.
      if (initial) {
        toast.error(
          error instanceof Error
            ? (error as any).message
            : "服务暂时不可用，请稍后重试",
        );
        pageState = "idle";
      }
    } finally {
      if (version === requestVersion) refreshing = false;
    }
  }

  function toggleSeat(seatId: SeatId) {
    if (!data || refreshing || submitting || pageState !== "ready") return;
    const seat = data.seats.find((candidate) => candidate.id === seatId);
    if (!seat || data.seatStates.get(seatId) !== "available") return;
    selected = toggleSeatSelection(
      selected,
      seatId,
      data.seats,
      data.seatStates,
    );
  }

  function clearSeats() {
    if (submitting || selected.size === 0) return;
    selected = clearSelection();
  }

  async function confirmSeats() {
    if (!data || submitting || refreshing || pageState !== "ready") return;
    if (!authentication.isLoggedIn) {
      toast.error("先登录，再挑座位");
      return;
    }
    if (selected.size === 0) {
      toast.error("先挑个座位吧");
      return;
    }
    const targetEventId = data.event.id;
    const seatIds = Object.freeze([...selected].sort((a, b) => a - b));
    submitting = true;
    try {
      await submitBooking(targetEventId, seatIds);
      toast.success("预约成功");
      selected = clearSelection();
      // Reload so the plan and the 3D scene reflect the new occupancy.
      await refresh();
    } catch (error: unknown) {
      toast.error(
        error instanceof Error
          ? (error as any).message
          : "预约失败，请稍后重试",
      );
      await refresh();
    } finally {
      submitting = false;
    }
  }

  // Reload whenever the route id changes; the component stays mounted across
  // detail navigations while the tab is active.
  $effect(() => {
    const currentEventId = eventId;
    untrack(() => {
      void refresh(true, currentEventId);
    });
    return () => {
      requestVersion++;
      loadController?.abort();
    };
  });

  onMount(() => {
    const update = () => {
      if (
        document.visibilityState === "visible" &&
        pageState === "ready" &&
        !refreshing &&
        !submitting
      )
        void refresh();
    };
    const poll = window.setInterval(update, 30000);
    window.addEventListener("focus", update);
    document.addEventListener("visibilitychange", update);
    return () => {
      window.clearInterval(poll);
      window.removeEventListener("focus", update);
      window.removeEventListener("visibilitychange", update);
    };
  });
</script>

{#if pageState === "loading"}
  <!-- TODO: show a skeleton placeholder while the seat map is loading. -->
{:else if data}
  <SeatBookingSection
    {data}
    selectedSeatIds={selected}
    {refreshing}
    {submitting}
    onSeatToggle={toggleSeat}
    onClear={clearSeats}
    onConfirm={() => {
      void confirmSeats();
    }}
  />
{/if}
