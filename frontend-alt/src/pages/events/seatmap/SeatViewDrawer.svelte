<script lang="ts">
  import * as Drawer from "$lib/components/ui/drawer";

  import SeatViewScene from "./SeatViewScene.svelte";
  import type { StaticSeat } from "@/common/api";

  // Shared seat perspective drawer; the 3D scene stays unmounted until a
  // focal seat is provided, so closing the drawer releases the WebGL context.
  // `let` is required here: a `const` $props() destructure cannot be a bind
  // target (svelte constant_binding).
  let {
    open = $bindable(false),
    focusSeat,
    seats,
  }: {
    open?: boolean;
    focusSeat: StaticSeat | null;
    seats: readonly StaticSeat[];
  } = $props();
</script>

<Drawer.Root bind:open>
  <Drawer.Content class={["h-[85vh]", "px-8", "flex", "flex-col"]}>
    <Drawer.Title class={["px-4", "py-8", "shrink-0"]}>
      {focusSeat?.label ?? ""} 视角
    </Drawer.Title>
    {#if focusSeat}
      <div class={["grow", "min-h-0", "px-4"]}>
        <SeatViewScene {seats} focusSeat={focusSeat} />
      </div>
    {/if}
    <!-- No actions here, but the footer band is kept so the layout matches
    the login and create drawers. -->
    <Drawer.Footer class={["px-4", "py-8"]}>
      <p class={["text-sm", "text-muted-foreground"]}>
        拖动环视场馆，滚轮缩放视野
      </p>
    </Drawer.Footer>
  </Drawer.Content>
</Drawer.Root>
