<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { toast } from "svelte-sonner";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { Button } from "$lib/components/ui/button";
  import ErrorState from "@/common/Error.svelte";
  import SeatBookingSection from "./components/SeatBookingSection.svelte";
  import BookingResult from "./BookingResult.svelte";
  import { loadSeatMap, submitBooking } from "./api";
  import { SeatMapSession, seatMapBlockReason } from "./session";

  const {
    eventId,
    onShowDetails,
  }: { eventId: number; onShowDetails?: () => void } = $props();
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
    await session.confirm(now);
    if (session.state.completed?.event.id === eventId) {
      window.dispatchEvent(
        new CustomEvent("seatverse:booking-created", { detail: { eventId } }),
      );
    }
  }

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

<nav class="px-6 py-3 flex flex-wrap gap-2" aria-label="选座导航">
  {#if onShowDetails}
    <Button variant="secondary" onclick={onShowDetails}>活动详情</Button>
  {:else}
    <Button variant="secondary" href={`#/events/${eventId}`}>活动详情</Button>
  {/if}
  <Button variant="secondary" href="#/events">活动列表</Button>
</nav>
{#if view.pageState === "loading"}
  <p class="px-6 py-12" role="status">正在加载活动与座位…</p>
{:else if view.pageState === "error"}
  <ErrorState
    description={view.loadingError}
    reloadCallback={() => {
      void session.open(eventId);
    }}
  />
{:else if view.data}
  <div class="px-6 py-3 flex flex-col gap-2">
    {#if !authentication.isLoggedIn}
      <p role="status">当前可浏览座位，请通过右上角账户入口登录后预约。</p>
      <Button
        variant="secondary"
        onclick={() => {
          window.dispatchEvent(new Event("seatverse:login-requested"));
        }}>登录后继续选座</Button
      >
    {/if}
    {#if view.refreshError}
      <p class="text-destructive" role="alert">
        {view.refreshError}，请刷新座位后继续。
      </p>
    {/if}
    {#if view.notice}<p class="text-destructive" role="alert">
        {view.notice}
      </p>{/if}
    {#if disabledReason}<p role="status">{disabledReason}</p>{/if}
    <div class="flex items-center justify-between gap-3">
      <p aria-live="polite">{view.feedback} · 已选 {view.selected.size} 座</p>
      <Button
        variant="secondary"
        disabled={view.submitting || view.refreshing}
        onclick={() => {
          void session.refresh();
        }}>刷新座位</Button
      >
    </div>
    {#if view.completed}
      <BookingResult booking={view.completed} {onShowDetails} />
    {/if}
  </div>
  <SeatBookingSection
    data={view.data}
    {now}
    showEventDetails={!onShowDetails}
    selectedSeatIds={view.selected}
    refreshing={view.refreshing}
    submitting={view.submitting}
    selectionDisabled={Boolean(disabledReason)}
    confirmDisabled={!authentication.isLoggedIn || Boolean(disabledReason)}
    onSeatToggle={(id) => session.toggle(id, now)}
    onClear={() => session.clear()}
    onConfirm={() => {
      void confirmSeats();
    }}
  />
{/if}
