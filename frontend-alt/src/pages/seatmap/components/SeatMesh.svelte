<script lang="ts">
  import { T, useThrelte } from "@threlte/core";
  import {
    createSeatObject,
    setSeatAppearance,
    type VenueResources,
  } from "@/pages/seatmap/scene-model";
  import type { SeatVisualState, StaticSeat } from "@/pages/seatmap/types";

  const props: {
    seat: StaticSeat;
    resources: VenueResources;
    visualState: SeatVisualState;
  } = $props();
  const { invalidate } = useThrelte();
  const object = $derived(createSeatObject(props.seat, props.resources));
  $effect(() => {
    setSeatAppearance(object, props.resources, props.visualState);
    invalidate();
  });
</script>

<!-- Shared geometries and materials are released by the scene; a single seat
never releases them on its own. -->
<T is={object} dispose={false} />
