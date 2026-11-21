<script lang="ts">
  import { RiBox3Line, RiCheckLine, RiEraserLine } from "remixicon-svelte";

  import Button from "$lib/components/ui/button/button.svelte";

  import SeatPlan from "./SeatPlan.svelte";
  import SeatScene from "./SeatScene.svelte";
  import type { SeatId, SeatMapData, SelectedSeatIds } from "../types";

  // Presentation-only seat booking view. All requests and selection state
  // live in the `SeatBooking` container; this component renders the flat
  // plan or the 3D panorama plus the action buttons.
  const {
    data,
    selectedSeatIds,
    refreshing,
    submitting,
    onSeatToggle,
    onClear,
    onConfirm,
  }: {
    data: SeatMapData;
    selectedSeatIds: SelectedSeatIds;
    refreshing: boolean;
    submitting: boolean;
    onSeatToggle: (seatId: SeatId) => void;
    onClear: () => void;
    onConfirm: () => void;
  } = $props();

  // Pure view state; switching modes never touches the shared selection.
  let immersive = $state(false);
</script>

<div class={["h-120", "px-6"]}>
  {#if immersive}
    <SeatScene
      seats={data.seats}
      seatStates={data.seatStates}
      {selectedSeatIds}
      disabled={refreshing || submitting}
      {onSeatToggle}
    />
  {:else}
    <SeatPlan
      seats={data.seats}
      seatStates={data.seatStates}
      {selectedSeatIds}
      disabled={refreshing || submitting}
      {onSeatToggle}
    />
  {/if}
</div>
<div class={["mt-4", "px-6", "flex", "items-center", "justify-end", "gap-3"]}>
  <Button
    variant={immersive ? "default" : "secondary"}
    size="icon"
    aria-label="沉浸选座"
    title="沉浸选座"
    onclick={() => (immersive = !immersive)}
  >
    <RiBox3Line />
  </Button>
  <Button
    variant="secondary"
    size="icon"
    aria-label="清空选择"
    title="清空选择"
    disabled={selectedSeatIds.size === 0 || submitting}
    onclick={onClear}
  >
    <RiEraserLine />
  </Button>
  <Button
    disabled={selectedSeatIds.size === 0 || submitting || refreshing}
    onclick={onConfirm}
  >
    <RiCheckLine />
    确认
  </Button>
</div>
