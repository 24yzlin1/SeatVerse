<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { toast } from "svelte-sonner";
  import { authentication } from "@/common/stores/authentication.svelte";
  import ErrorState from "@/common/Error.svelte";
  import {
    SeatMapSession,
    loadSeatMap,
    seatMapBlockReason,
    submitBooking,
  } from "@/common/api";
  import SeatBookingSection from "@/pages/events/seatmap/SeatBookingSection.svelte";

  const {
    eventId,
  }: { eventId: number } = $props();
  const session = new SeatMapSession(
    { loadSeatMap, submitBooking },
    (state) => {
      view = state;
    },
  );
  let view = $state.raw(session.state);
  let now = $state(Date.now());
  const disabledReason = $derived(seatMapBlockReason(view, now));

  async function confirmSeats() {
    if (!authentication.isLoggedIn) {
      toast.error("请先通过右上角账户入口登录，再确认座位");
      return;
    }
    const blockReason = disabledReason;
    if (blockReason) {
      toast.error(blockReason);
      return;
    }
    await session.confirm(now);
    if (session.state.completed?.event.id === eventId) {
      toast.success("预约成功");
      window.dispatchEvent(
        new CustomEvent("seatverse:booking-created", { detail: { eventId } }),
      );
    }
    if (session.state.notice) {
      toast.error(session.state.notice);
    }
  }

  // Failures surface as toasts instead of inline partial error blocks.
  // Consecutive identical poll failures only notify once per episode.
  let reportedRefreshError = "";
  $effect(() => {
    const refreshError = view.refreshError;
    if (refreshError && refreshError !== reportedRefreshError) {
      reportedRefreshError = refreshError;
      toast.error(refreshError);
    } else if (!refreshError) {
      reportedRefreshError = "";
    }
  });

  $effect(() => {
    const id = eventId;
    // Account changes must not inherit choices or a private receipt.
    const identity = authentication.user?.id ?? null;
    untrack(() => {
      void session.open(id);
    });
    void identity;
    return () => session.dispose();
  });

  onMount(() => {
    const update = () => {
      now = Date.now();
      if (
        document.visibilityState === "visible" &&
        view.pageState === "ready" &&
        !view.refreshing &&
        !view.submitting
      ) {
        void session.refresh();
      }
    };
    const clock = window.setInterval(() => {
      now = Date.now();
    }, 1000);
    const poll = window.setInterval(update, 30000);
    window.addEventListener("focus", update);
    document.addEventListener("visibilitychange", update);
    window.addEventListener("seatverse:booking-cancelled", update);
    return () => {
      window.clearInterval(clock);
      window.clearInterval(poll);
      window.removeEventListener("focus", update);
      document.removeEventListener("visibilitychange", update);
      window.removeEventListener("seatverse:booking-cancelled", update);
    };
  });
</script>

{#if view.pageState === "loading"}
  <!-- Blank while loading; the seat map replaces this branch once ready. -->
{:else if view.pageState === "error"}
  <ErrorState
    description={view.loadingError}
    reloadCallback={() => {
      void session.open(eventId);
    }}
  />
{:else if view.data}
  <SeatBookingSection
    data={view.data}
    selectedSeatIds={view.selected}
    refreshing={view.refreshing}
    submitting={view.submitting}
    selectionDisabled={Boolean(disabledReason)}
    onSeatToggle={(id) => session.toggle(id, now)}
    onClear={() => session.clear()}
    onConfirm={() => {
      void confirmSeats();
    }}
  />
{/if}
