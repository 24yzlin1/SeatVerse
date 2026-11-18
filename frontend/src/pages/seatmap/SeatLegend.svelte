<script lang="ts">
  import type { SeatVisualState } from "./types";

  const entries: readonly [SeatVisualState, string][] = [
    ["available", "可选"],
    ["sold", "已预约"],
    ["selected", "本地已选"],
    ["unavailable", "锁定 / 状态未知"],
  ];
</script>

<div class="seat-legend" aria-label="3D 与平面选座共用图例">
  {#each entries as [state, label] (state)}
    <span><i data-seat-state={state} aria-hidden="true"></i>{label}</span>
  {/each}
</div>

<style>
  .seat-legend {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 18px;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    color: var(--muted-foreground);
  }
  span {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  i {
    width: 13px;
    height: 13px;
    border-radius: 4px 4px 2px 2px;
    border: 1px solid transparent;
  }
  [data-seat-state="available"] {
    background: var(--seat-available);
  }
  [data-seat-state="sold"] {
    background: var(--seat-sold);
  }
  [data-seat-state="selected"] {
    background: var(--seat-selected);
    border: 2px solid var(--seat-selected-foreground);
  }
  [data-seat-state="unavailable"] {
    background: var(--seat-unavailable);
    border: 1px dashed var(--foreground);
  }
</style>
