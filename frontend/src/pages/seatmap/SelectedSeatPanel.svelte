<script lang="ts">
  import type { SeatId, StaticSeat } from "./types";
  interface Props {
    seats: readonly StaticSeat[];
    submitting: boolean;
    disabledReason: string;
    feedback: string;
    loggedIn: boolean;
    onSeatToggle: (id: SeatId) => void;
    onClear: () => void;
    onSubmit: () => void;
  }
  const props: Props = $props();
</script>

<aside class="selection-panel" aria-labelledby="selection-title">
  <p class="eyebrow">选座确认</p>
  <h2 id="selection-title">已选 {props.seats.length} 座</h2>
  <p class="feedback" role="status" aria-live="polite">{props.feedback}</p>
  {#if props.seats.length > 0}
    <ul aria-label="已选座位">
      {#each props.seats as seat (seat.id)}
        <li>
          <span>{seat.label}</span><button
            type="button"
            disabled={props.submitting}
            aria-label={`移除${seat.label}`}
            onclick={() => props.onSeatToggle(seat.id)}>移除</button
          >
        </li>
      {/each}
    </ul>
  {:else}<p class="hint">在 3D 或平面图中点击可选座位。</p>{/if}
  <button
    type="button"
    class="clear"
    disabled={props.submitting || props.seats.length === 0}
    onclick={props.onClear}>清空选择</button
  >
  <button
    type="button"
    class="confirm"
    disabled={props.submitting ||
      Boolean(props.disabledReason) ||
      (props.loggedIn && props.seats.length === 0)}
    onclick={props.onSubmit}
  >
    {props.submitting
      ? "正在确认预约…"
      : !props.loggedIn
        ? "登录后继续选座"
        : `确认选座（${props.seats.length} 座）`}
  </button>
  {#if props.disabledReason}<p class="reason" role="status">
      {props.disabledReason}
    </p>{/if}
  <p class="hint">选中尚未锁座。确认后将创建实际预约，最终结果以服务器为准。</p>
  <a href="#/bookings">查看我的预约</a>
</aside>

<style>
  .selection-panel {
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
  .feedback {
    margin: 14px 0;
    font-size: 13px;
    line-height: 1.7;
  }
  ul {
    max-height: 240px;
    overflow-y: auto;
    border-block: 1px solid var(--border);
  }
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    font-size: 13px;
  }
  button {
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 8px 12px;
    font-size: 12px;
    cursor: pointer;
  }
  button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
  button:focus-visible,
  a:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 3px;
  }
  .clear {
    margin-top: 16px;
  }
  .confirm {
    display: block;
    width: 100%;
    margin-top: 12px;
    min-height: 44px;
    background: var(--primary);
    color: var(--primary-foreground);
    font-size: 14px;
    font-weight: 600;
  }
  .hint,
  .reason {
    margin-top: 14px;
    font-size: 12px;
    line-height: 1.8;
    color: var(--muted-foreground);
  }
  .reason {
    color: var(--destructive);
  }
  a {
    display: inline-block;
    margin-top: 16px;
    font-size: 12px;
    text-decoration: underline;
    text-underline-offset: 3px;
  }
</style>
