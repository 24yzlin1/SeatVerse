<script lang="ts">
  import {
    RiBox3Line,
    RiCheckLine,
    RiEraserLine,
    RiLoader4Line,
  } from "remixicon-svelte";

  import { Button } from "$lib/components/ui/button";

  import SeatPlan from "./SeatPlan.svelte";
  import SeatScene from "./SeatScene.svelte";
  import {
    SEAT_VISUAL_LABEL,
    seatVisualState,
  } from "@/common/utils/seatSelection";
  import type {
    SeatId,
    SeatMapData,
    SelectedSeatIds,
  } from "@/common/api";

  // Presentation-only seat booking view. All requests and selection state
  // live in the `SeatBooking` container; this component renders the flat
  // plan or the 3D panorama plus the action buttons.
  const {
    data,
    selectedSeatIds,
    refreshing,
    submitting,
    selectionDisabled = false,
    confirmDisabled = false,
    onSeatToggle,
    onClear,
    onConfirm,
  }: {
    data: SeatMapData;
    selectedSeatIds: SelectedSeatIds;
    refreshing: boolean;
    submitting: boolean;
    selectionDisabled?: boolean;
    confirmDisabled?: boolean;
    onSeatToggle: (seatId: SeatId) => void;
    onClear: () => void;
    onConfirm: () => void;
  } = $props();

  // Pure view state; switching modes never touches the shared selection.
  let immersive = $state(false);
  let resetVersion = $state(0);
  let hoveredSeatId = $state<SeatId | null>(null);
  const selectedSeats = $derived(
    data.seats
      .filter((seat) => selectedSeatIds.has(seat.id))
      .toSorted((a, b) => a.row - b.row || a.number - b.number),
  );
  const hoveredSeat = $derived(
    data.seats.find((seat) => seat.id === hoveredSeatId),
  );
</script>

<div class="h-120 px-6">
  {#if immersive}
    <SeatScene
      seats={data.seats}
      seatStates={data.seatStates}
      {selectedSeatIds}
      disabled={refreshing || submitting || selectionDisabled}
      {onSeatToggle}
      {resetVersion}
      onSeatHover={(id) => (hoveredSeatId = id)}
      onUnavailable={() => {
        immersive = false;
        hoveredSeatId = null;
      }}
    />
  {:else}
    <SeatPlan
      seats={data.seats}
      seatStates={data.seatStates}
      {selectedSeatIds}
      disabled={refreshing || submitting || selectionDisabled}
      {onSeatToggle}
      onSeatHover={(id) => (hoveredSeatId = id)}
    />
  {/if}
</div>
<p class="sr-only" role="status">
  {#if hoveredSeat}
    {hoveredSeat.label} · {SEAT_VISUAL_LABEL[
      seatVisualState(hoveredSeat.id, data.seatStates, selectedSeatIds)
    ]}
  {/if}
</p>
<section
  class="sticky bottom-0 z-9 h-14 px-6 flex items-center justify-between gap-4 bg-background/80 backdrop-blur-xs"
  aria-label="预约确认"
>
  <div class="flex items-center gap-2 shrink-0">
    <Button
      variant={immersive ? "default" : "secondary"}
      size="icon"
      aria-label={immersive ? "切换到平面选座" : "切换到3D选座"}
      title={immersive ? "切换到平面选座" : "切换到3D选座"}
      onclick={() => {
        immersive = !immersive;
        resetVersion++;
        hoveredSeatId = null;
      }}
    >
      <RiBox3Line />
    </Button>
    <Button
      variant="secondary"
      size="icon"
      aria-label="清空选择"
      title="清空选择"
      disabled={selectedSeatIds.size === 0 || submitting || refreshing}
      onclick={onClear}
    >
      <RiEraserLine />
    </Button>
  </div>
  <Button
    aria-busy={submitting}
    disabled={selectedSeatIds.size === 0 ||
      submitting ||
      refreshing ||
      confirmDisabled}
    onclick={onConfirm}
  >
    {#if submitting}
      <RiLoader4Line data-icon="inline-start" class="animate-spin" />
      正在提交预约…
    {:else}
      <RiCheckLine data-icon="inline-start" />
      确认预约（{selectedSeats.length} 座）
    {/if}
  </Button>
</section>
