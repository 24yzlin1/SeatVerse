<script lang="ts">
  import { projectSeatToPlan, venueLayout } from "@/pages/seatmap/seat-layout";
  import { seatVisualState } from "@/pages/seatmap/selection";
  import type { SeatSceneProps, SeatVisualState } from "@/pages/seatmap/types";

  const props: SeatSceneProps = $props();
  const rows = $derived([
    ...new Map(props.seats.map((seat) => [seat.row, seat])).values(),
  ]);
  const labels: Record<SeatVisualState, string> = {
    available: "可选",
    sold: "已预约",
    selected: "本地已选",
    unavailable: "锁定或状态未知，不可选",
  };
  const width = venueLayout.halfWidth * 2;
  const depth = venueLayout.rear - venueLayout.front;
  const stage = projectSeatToPlan(venueLayout.stage);
  const aisle = projectSeatToPlan(venueLayout.aisle);
</script>

<div class="plan-scroll" role="group" aria-label="平面选座">
  <div class="seat-plan" style:aspect-ratio={width / depth}>
    <div
      class="plan-stage"
      style:left={`${stage.left}%`}
      style:top={`${stage.top}%`}
      style:width={`${(venueLayout.stage.width / width) * 100}%`}
      style:height={`${(venueLayout.stage.depth / depth) * 100}%`}
    >
      <strong>舞 台</strong><span>STAGE</span>
    </div>
    <div
      class="plan-aisle"
      aria-hidden="true"
      style:left={`${aisle.left}%`}
      style:top={`${aisle.top}%`}
      style:width={`${(venueLayout.aisle.width / width) * 100}%`}
      style:height={`${(venueLayout.aisle.depth / depth) * 100}%`}
    >
      <span>中央过道</span>
    </div>
    {#each rows as seat (seat.row)}
      <span class="row-label" style:top={`${projectSeatToPlan(seat).top}%`}
        >{seat.row}排</span
      >
    {/each}
    {#each props.seats as seat (seat.id)}
      {@const state = seatVisualState(
        seat.id,
        props.seatStates,
        props.selectedSeatIds,
      )}
      {@const position = projectSeatToPlan(seat)}
      <button
        type="button"
        class="plan-seat"
        data-seat-id={seat.id}
        data-seat-state={state}
        data-world-x={seat.x}
        data-world-y={seat.y}
        data-world-z={seat.z}
        style:left={`${position.left}%`}
        style:top={`${position.top}%`}
        aria-label={`${seat.label}，${labels[state]}`}
        aria-pressed={state === "selected"}
        title={`${seat.label} · ${labels[state]}`}
        disabled={props.disabled || state === "sold" || state === "unavailable"}
        onclick={() => props.onSeatToggle(seat.id)}
        onpointerenter={() => props.onSeatHover?.(seat.id)}
        onpointerleave={() => props.onSeatHover?.(null)}
        onfocus={() => props.onSeatHover?.(seat.id)}
        onblur={() => props.onSeatHover?.(null)}>{seat.number}</button
      >
    {/each}
    <p class="plan-entry">入口 / 后排</p>
  </div>
</div>

<style>
  .plan-scroll {
    height: 100%;
    width: 100%;
  }
  .seat-plan {
    position: relative;
    height: 100%;
    max-width: 100%;
    margin: 0 auto;
  }
  .plan-stage,
  .plan-aisle,
  .plan-seat {
    position: absolute;
    transform: translate(-50%, -50%);
  }
  .plan-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--border);
    border-radius: 8px 8px 28px 28px;
    background: var(--muted);
    color: var(--muted-foreground);
  }
  .plan-stage strong {
    font-weight: 500;
    font-size: 13px;
  }
  .plan-stage span {
    font-size: 9px;
    letter-spacing: 0.2em;
  }
  .plan-aisle {
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--muted);
    border-radius: 8px;
  }
  .plan-aisle span {
    writing-mode: vertical-rl;
    font-size: 10px;
    letter-spacing: 0.3em;
    color: var(--muted-foreground);
  }
  .row-label {
    position: absolute;
    left: 3%;
    transform: translateY(-50%);
    font-size: 11px;
    color: var(--muted-foreground);
  }
  .plan-seat {
    width: 4.25%;
    height: 4.25%;
    border: 1px solid transparent;
    border-radius: 7px 7px 3px 3px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    font-variant-numeric: tabular-nums;
  }
  [data-seat-state="available"] {
    background: var(--seat-available);
    color: var(--seat-available-foreground);
  }
  [data-seat-state="selected"] {
    background: var(--seat-selected);
    color: var(--seat-selected-foreground);
    border: 2px solid var(--seat-selected-foreground);
  }
  [data-seat-state="sold"] {
    background: var(--seat-sold);
    color: var(--seat-sold-foreground);
    text-decoration: line-through;
  }
  [data-seat-state="unavailable"] {
    background: var(--seat-unavailable);
    color: var(--seat-sold-foreground);
    border: 1px dashed var(--foreground);
  }
  .plan-seat:disabled {
    cursor: not-allowed;
  }
  .plan-seat:hover:enabled {
    outline: 2px solid var(--ring);
    outline-offset: 2px;
  }
  .plan-seat:focus-visible,
  .plan-scroll:focus-visible {
    outline: 2px solid var(--foreground);
    outline-offset: 3px;
  }
  .plan-entry {
    position: absolute;
    bottom: 1%;
    width: 100%;
    text-align: center;
    font-size: 11px;
    color: var(--muted-foreground);
  }
</style>
