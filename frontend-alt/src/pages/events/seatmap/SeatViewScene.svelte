<script lang="ts">
  import { Canvas } from "@threlte/core";
  import { AgXToneMapping, PCFShadowMap } from "three";

  import Error from "@/common/Error.svelte";

  import SeatViewWorld from "./SeatViewWorld.svelte";
  import type { StaticSeat } from "@/common/api";

  // Canvas wrapper for the read-only seat perspective preview; a WebGL
  // failure only degrades the drawer content, the booking flow stays usable.
  const props: {
    seats: readonly StaticSeat[];
    focusSeat: StaticSeat;
  } = $props();
  let failed = $state(false);
</script>

{#if !failed}
  <svelte:boundary
    onerror={() => {
      failed = true;
    }}
  >
    <Canvas
      renderMode="on-demand"
      shadows={PCFShadowMap}
      dpr={[1, 1.75]}
      toneMapping={AgXToneMapping}
    >
      <SeatViewWorld seats={props.seats} focusSeat={props.focusSeat} />
    </Canvas>
  </svelte:boundary>
{:else}
  <Error
    title="座位视角进不去"
    description="3D 渲染暂时失败，稍后再打开试试"
  />
{/if}
