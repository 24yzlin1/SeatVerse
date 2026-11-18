<script lang="ts">
  import { T, useThrelte } from "@threlte/core";
  import {
    createSeatObject,
    setSeatAppearance,
    type VenueResources,
  } from "./scene-model";
  import type { SeatVisualState, StaticSeat } from "./types";

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

<!-- 共享几何体和材质由场景统一释放，单座不重复释放。 -->
<T is={object} dispose={false} />
