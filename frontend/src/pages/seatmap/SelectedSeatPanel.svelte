<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import type { Booking } from "@/common/api";
  import { formatDateTime } from "@/common/utils/datetime";
  import type { SeatId, SeatMapData, StaticSeat } from "./types";

  interface Props {
    event: SeatMapData["event"];
    statusLabel: string;
    seats: readonly StaticSeat[];
    submitting: boolean;
    refreshing: boolean;
    disabledReason: string;
    feedback: string;
    submissionError: string;
    completed: Booking | null;
    loggedIn: boolean;
    onSeatToggle: (id: SeatId) => void;
    onClear: () => void;
    onSubmit: () => void;
  }

  const props: Props = $props();
  let resultHeading = $state<HTMLHeadingElement>();
  const editingDisabled = $derived(props.submitting || props.refreshing);
  const confirmDisabled = $derived(
    editingDisabled ||
      Boolean(props.disabledReason) ||
      props.seats.length === 0,
  );
  const reason = $derived(
    props.disabledReason ||
      (props.refreshing
        ? "正在更新座位状态"
        : props.seats.length === 0 && !props.completed
          ? "请选择至少一个可选座位"
          : ""),
  );

  $effect(() => {
    if (props.completed && resultHeading) resultHeading.focus();
  });
</script>

<aside
  id="selected-seat-panel"
  class="selection-panel"
  aria-labelledby="selection-title"
>
  <p class="eyebrow">选座确认</p>
  <h2 id="selection-title" tabindex="-1">已选 {props.seats.length} 座</h2>
  <section class="event-summary" aria-label="本次预约活动">
    <h3>{props.event.title}</h3>
    <p>{props.event.venue.name}</p>
    <p class="period">
      <time datetime={props.event.startTime}
        >{formatDateTime(props.event.startTime)}</time
      >
      <span>至</span>
      <time datetime={props.event.endTime}
        >{formatDateTime(props.event.endTime)}</time
      >
    </p>
    <span class="event-status">{props.statusLabel}</span>
  </section>

  <p class="feedback" role="status" aria-live="polite">{props.feedback}</p>
  {#if props.seats.length > 0}
    <ul aria-label="已选座位">
      {#each props.seats as seat (seat.id)}
        <li>
          <span>{seat.label}</span>
          <Button
            variant="ghost"
            size="sm"
            class="min-h-11"
            disabled={editingDisabled}
            aria-label={`移除${seat.label}`}
            onclick={() => props.onSeatToggle(seat.id)}>移除</Button
          >
        </li>
      {/each}
    </ul>
  {:else if !props.completed && !props.disabledReason}
    <p class="hint">在 3D 或平面图中点击可选座位，再在此核对并确认。</p>
  {/if}

  <div class="actions">
    <Button
      variant="outline"
      class="min-h-11"
      disabled={editingDisabled || props.seats.length === 0}
      onclick={props.onClear}>清空选择</Button
    >
    <Button
      id="selection-confirm"
      class="h-11 w-full"
      disabled={confirmDisabled}
      aria-busy={props.submitting}
      aria-describedby={reason ? "selection-block-reason" : undefined}
      onclick={props.onSubmit}
    >
      {props.submitting
        ? "正在确认预约…"
        : !props.loggedIn
          ? "登录后继续选座"
          : `确认选座（${props.seats.length} 座）`}
    </Button>
  </div>
  {#if reason}
    <p id="selection-block-reason" class="reason">{reason}</p>
  {/if}
  {#if props.submissionError}
    <p class="submission-error" role="alert">{props.submissionError}</p>
  {/if}

  {#if props.completed}
    <section class="booking-result" role="status" aria-label="预约成功">
      <h3 bind:this={resultHeading} tabindex="-1">预约成功</h3>
      <p>{props.completed.seats.map((seat) => seat.label).join("、")}</p>
      <dl>
        <div>
          <dt>预约编号</dt>
          <dd>{props.completed.id}</dd>
        </div>
        <div>
          <dt>票号</dt>
          <dd>{props.completed.ticketCode}</dd>
        </div>
      </dl>
    </section>
  {/if}

  <p class="hint">选中尚未锁座。确认后将创建实际预约，最终结果以服务器为准。</p>
  <a class="bookings-link" href="#/bookings">查看我的预约</a>
</aside>

<style>
  .selection-panel {
    position: sticky;
    top: 80px;
    max-height: calc(100dvh - 100px);
    overflow-y: auto;
    scroll-margin-top: 88px;
    padding: 24px;
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    background: var(--card);
  }
  .eyebrow {
    font-size: 12px;
    color: var(--muted-foreground);
    margin-bottom: 8px;
  }
  h2 {
    font-size: 24px;
    font-weight: 650;
  }
  .event-summary {
    margin-top: 18px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    line-height: 1.8;
    color: var(--muted-foreground);
  }
  .event-summary h3 {
    color: var(--foreground);
    font-size: 14px;
    font-weight: 600;
    overflow-wrap: anywhere;
  }
  .event-summary p {
    margin-top: 6px;
  }
  .period {
    display: grid;
    gap: 2px;
  }
  .event-status {
    display: inline-block;
    margin-top: 8px;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    background: var(--secondary);
    color: var(--secondary-foreground);
  }
  .feedback {
    margin: 14px 0;
    font-size: 13px;
    line-height: 1.7;
  }
  ul {
    max-height: min(240px, 25dvh);
    overflow-y: auto;
    border-block: 1px solid var(--border);
  }
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    font-size: 13px;
  }
  .actions {
    display: grid;
    justify-items: start;
    gap: 12px;
    margin-top: 16px;
  }
  .hint,
  .reason,
  .submission-error {
    margin-top: 14px;
    font-size: 12px;
    line-height: 1.8;
    color: var(--muted-foreground);
  }
  .reason,
  .submission-error {
    color: var(--destructive);
  }
  .booking-result {
    margin-top: 18px;
    padding: 16px;
    border: 1px solid var(--seat-available);
    border-radius: var(--radius);
    font-size: 12px;
    line-height: 1.8;
    overflow-wrap: anywhere;
  }
  .booking-result h3 {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 6px;
  }
  dl {
    margin-top: 10px;
  }
  dt {
    color: var(--muted-foreground);
  }
  dd {
    font-variant-numeric: tabular-nums;
  }
  .bookings-link {
    display: inline-block;
    margin-top: 16px;
    font-size: 12px;
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  a:focus-visible,
  h3:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 3px;
  }
  @media (max-width: 800px) {
    .selection-panel {
      position: static;
      max-height: none;
      overflow-y: visible;
    }
    ul {
      max-height: 240px;
    }
  }
</style>
