<script lang="ts">
  import {
    RiBox3Line,
    RiCheckLine,
    RiCloseLine,
    RiEraserLine,
    RiLoader4Line,
    RiRestartLine,
  } from "remixicon-svelte";

  import { Button } from "$lib/components/ui/button";

  import SeatPlan from "./SeatPlan.svelte";
  import SeatScene from "./SeatScene.svelte";
  import SeatLegend from "./SeatLegend.svelte";
  import SeatEventSummary from "./SeatEventSummary.svelte";
  import {
    SEAT_VISUAL_LABEL,
    seatVisualState,
  } from "@/pages/seatmap/selection";
  import type {
    SeatId,
    SeatMapData,
    SelectedSeatIds,
  } from "@/pages/seatmap/types";

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
    showEventDetails = true,
    now = Date.now(),
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
    showEventDetails?: boolean;
    now?: number;
    onSeatToggle: (seatId: SeatId) => void;
    onClear: () => void;
    onConfirm: () => void;
  } = $props();

  // Pure view state; switching modes never touches the shared selection.
  let immersive = $state(false);
  let resetVersion = $state(0);
  let hoveredSeatId = $state<SeatId | null>(null);
  let sceneUnavailable = $state(false);
  const selectedSeats = $derived(
    data.seats
      .filter((seat) => selectedSeatIds.has(seat.id))
      .toSorted((a, b) => a.row - b.row || a.number - b.number),
  );
  const hoveredSeat = $derived(
    data.seats.find((seat) => seat.id === hoveredSeatId),
  );
</script>

<div class="px-6 py-3 flex flex-col gap-4">
  {#if showEventDetails}
    <SeatEventSummary event={data.event} {now} />
  {/if}
  <SeatLegend />
  {#if sceneUnavailable}
    <p role="status" class="text-sm text-muted-foreground">
      3D 视角暂不可用，已切换到平面选座；你的选择已保留。
    </p>
  {/if}
</div>
<div class={["h-120", "px-6"]}>
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
        sceneUnavailable = true;
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
<p class="px-6 py-3 text-sm text-muted-foreground" role="status">
  {#if hoveredSeat}
    {hoveredSeat.label} · {SEAT_VISUAL_LABEL[
      seatVisualState(hoveredSeat.id, data.seatStates, selectedSeatIds)
    ]}
  {:else if immersive}
    拖动旋转，滚轮或双指缩放；悬停或点击座位可查看排号和座号。
  {:else}
    点击可选座位进行选择，再次点击即可取消。
  {/if}
</p>
<section
  class="sticky bottom-0 px-6 py-4 flex flex-col gap-3 border-t bg-background/95 backdrop-blur-sm"
  aria-label="预约确认"
>
  <div class="flex flex-wrap items-center justify-between gap-2">
    <h2 class="font-medium">已选 {selectedSeats.length} 座</h2>
    <p class="text-sm text-muted-foreground">
      本地选择不锁座，提交后才确认预约。
    </p>
  </div>
  {#if selectedSeats.length === 0}
    <p class="text-sm text-muted-foreground">
      尚未选择座位，请先选择可选座位。
    </p>
  {:else}
    <ul
      class="max-h-28 overflow-y-auto flex flex-wrap gap-2"
      aria-label="已选座位"
    >
      {#each selectedSeats as seat (seat.id)}
        <li>
          <Button
            variant="secondary"
            size="sm"
            aria-label={`移除${seat.label}`}
            disabled={submitting || refreshing}
            onclick={() => onSeatToggle(seat.id)}
          >
            {seat.label}<RiCloseLine data-icon="inline-end" />
          </Button>
        </li>
      {/each}
    </ul>
  {/if}
  <div class="flex flex-wrap items-center justify-end gap-2">
    <Button
      variant={immersive ? "default" : "secondary"}
      size="icon"
      aria-label={immersive ? "切换到平面选座" : "切换到3D选座"}
      title={immersive ? "切换到平面选座" : "切换到3D选座"}
      onclick={() => {
        immersive = !immersive;
        hoveredSeatId = null;
        sceneUnavailable = false;
      }}
    >
      <RiBox3Line />
    </Button>
    <Button
      variant="secondary"
      size="icon"
      aria-label="重置视角"
      title="重置视角"
      disabled={!immersive}
      onclick={() => {
        resetVersion++;
        hoveredSeatId = null;
      }}
    >
      <RiRestartLine />
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
  </div>
</section>
