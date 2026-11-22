<script lang="ts">
  import { Canvas } from "@threlte/core";
  import { toast } from "svelte-sonner";
  import { AgXToneMapping, PCFShadowMap } from "three";

  import VenueScene from "./VenueScene.svelte";
  import type { SeatSceneProps } from "./types";

  const props: SeatSceneProps & { onUnavailable?: () => void } = $props();
  let failed = $state(false);
</script>

<div class={["relative", "h-full", "w-full"]}>
  {#if !failed}
    <svelte:boundary
      onerror={() => {
        failed = true;
        // A WebGL failure only breaks the 3D view; the flat plan stays
        // usable, so surface the issue as a toast instead of a full error.
        toast.error("3D 视角暂时进不去，先看看平面图吧");
        props.onUnavailable?.();
      }}
    >
      <Canvas
        renderMode="on-demand"
        shadows={PCFShadowMap}
        dpr={[1, 1.75]}
        toneMapping={AgXToneMapping}
      >
        <VenueScene
          seats={props.seats}
          seatStates={props.seatStates}
          selectedSeatIds={props.selectedSeatIds}
          disabled={props.disabled}
          onSeatToggle={props.onSeatToggle}
          onSeatHover={props.onSeatHover}
          resetVersion={props.resetVersion}
        />
      </Canvas>
    </svelte:boundary>
  {:else}
    <p role="status">3D 视角暂不可用，请切换到平面选座继续。</p>
  {/if}
</div>
