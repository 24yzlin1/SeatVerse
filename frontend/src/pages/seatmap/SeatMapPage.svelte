<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { navigate, router } from "@/common/router";
  import { auth } from "@/common/stores/auth.svelte";
  import Loading from "@/common/components/Loading.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import SeatSelectionPage from "./SeatSelectionPage.svelte";
  import { loadSeatMap, submitBooking } from "./api";
  import { SeatMapSession, seatMapBlockReason } from "./session";

  const rawId = $derived(router.params.id ?? "");
  const eventId = $derived(
    /^[1-9]\d*$/.test(rawId) && Number.isSafeInteger(Number(rawId))
      ? Number(rawId)
      : Number.NaN,
  );
  const session = new SeatMapSession(
    { loadSeatMap, submitBooking },
    (state) => {
      view = state;
    },
  );
  let view = $state.raw(session.state);
  let now = $state(Date.now());
  const data = $derived(view.data);
  const disabledReason = $derived(seatMapBlockReason(view, now));
  const selectionDisabled = $derived(
    view.submitting || Boolean(disabledReason) || view.pageState !== "ready",
  );

  function confirmSeats() {
    if (!data || view.submitting || disabledReason || view.selected.size === 0)
      return;
    if (!auth.isLoggedIn) {
      navigate(
        `/login?next=${encodeURIComponent(`/events/${eventId}/seats`)}`,
      );
      return;
    }
    void session.confirm(now);
  }

  $effect(() => {
    const id = eventId;
    untrack(() => {
      void session.open(id);
    });
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
      )
        void session.refresh();
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

{#if view.pageState === "loading"}
  <section class="loading-page" aria-label="正在加载活动与座位">
    <Loading />
  </section>
{:else if view.pageState === "error"}
  <section class="loading-page">
    <ErrorState message={view.loadingError} />
    <div class="actions">
      <button type="button" onclick={() => session.open(eventId)}
        >重新加载</button
      ><a href="#/events">返回活动列表</a>
    </div>
  </section>
{:else if data}
  <div class="notifications">
    {#if view.refreshError}<p class="alert" role="alert">
        {view.refreshError}，请刷新座位后继续。
      </p>{/if}
  </div>
  <SeatSelectionPage
    {data}
    selectedSeatIds={view.selected}
    submitting={view.submitting}
    refreshing={view.refreshing}
    {disabledReason}
    {selectionDisabled}
    feedback={view.feedback}
    submissionError={view.notice}
    completed={view.completed}
    {now}
    loggedIn={auth.isLoggedIn}
    onSeatToggle={(id) => session.toggle(id, now)}
    onClear={() => session.clear()}
    onSubmit={confirmSeats}
    onRefresh={() => session.refresh()}
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
  .alert {
    margin-top: 20px;
    padding: 18px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    line-height: 1.8;
  }
  .alert {
    color: var(--destructive);
  }
</style>
