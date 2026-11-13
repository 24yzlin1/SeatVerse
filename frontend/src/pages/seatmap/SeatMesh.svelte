<script lang="ts">
  import { T } from "@threlte/core";
  import { createSeatObject, type VenueResources } from "./scene-model";
  import type { StaticSeat } from "./types";

  const props: { seat: StaticSeat; resources: VenueResources } = $props();
  const object = $derived(createSeatObject(props.seat, props.resources));
</script>

<!-- 共享几何体和材质由场景统一释放，单座不重复释放。 -->
<T is={object} dispose={false} />
