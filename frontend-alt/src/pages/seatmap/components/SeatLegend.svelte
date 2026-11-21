<script lang="ts">
  import { SEAT_VISUAL_LABEL } from "@/pages/seatmap/selection";
  import type { SeatVisualState } from "@/pages/seatmap/types";

  const states: readonly SeatVisualState[] = [
    "available",
    "sold",
    "selected",
    "unavailable",
  ];
</script>

<ul class="flex flex-wrap gap-x-4 gap-y-2 text-sm" aria-label="座位状态图例">
  {#each states as state (state)}
    <li class="flex items-center gap-2">
      <span
        class="size-3 rounded-sm border border-foreground/30"
        style:background={`var(--seat-${state})`}
        aria-hidden="true"
      ></span>
      {SEAT_VISUAL_LABEL[state]}
    </li>
  {/each}
</ul>
