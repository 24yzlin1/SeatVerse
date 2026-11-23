<script lang="ts">
  import { projectSeatToPlan, venueLayout } from "./seat-layout";
  import {
    SEAT_VISUAL_LABEL,
    seatVisualState,
  } from "@/common/utils/seatSelection";
  import type { SeatVisualState } from "@/common/utils/seatSelection";
  import type { SeatSceneProps } from "./types";

  const props: SeatSceneProps = $props();
  const rows = $derived([
    ...new Map(props.seats.map((seat) => [seat.row, seat])).values(),
  ]);
  const width = venueLayout.halfWidth * 2;
  const depth = venueLayout.rear - venueLayout.front;
  const stage = projectSeatToPlan(venueLayout.stage);
  const aisle = projectSeatToPlan(venueLayout.aisle);

  // Tailwind palette keyed by the shared visual state; replacing the scoped
  // stylesheet keeps styling declarative next to the markup.
  const SEAT_STATE_CLASS: Record<SeatVisualState, string[]> = {
    available: [
      "bg-(--seat-available)",
      "text-(--seat-available-foreground)",
      "border",
      "border-transparent",
    ],
    selected: [
      "bg-(--seat-selected)",
      "text-(--seat-selected-foreground)",
      "border-2",
      "border-(--seat-selected-foreground)",
    ],
    sold: [
      "bg-(--seat-sold)",
      "text-(--seat-sold-foreground)",
      "border",
      "border-transparent",
      "line-through",
    ],
    unavailable: [
      "bg-(--seat-unavailable)",
      "text-(--seat-sold-foreground)",
      "border",
      "border-dashed",
      "border-(--foreground)",
    ],
  };
</script>

<div
  class={["h-full", "w-full", "focus-visible:outline-2", "focus-visible:outline-(--foreground)", "focus-visible:outline-offset-3"]}
  role="group"
  aria-label="平面选座"
>
  <div
    class={["relative", "h-full", "max-w-full", "mx-auto"]}
    style:aspect-ratio={width / depth}
  >
    <div
      class={["absolute", "-translate-x-1/2", "-translate-y-1/2", "flex", "flex-col", "items-center", "justify-center", "gap-1.5", "border", "border-(--border)", "rounded-t-lg", "rounded-b-[28px]", "bg-(--muted)", "text-(--muted-foreground)"]}
      style:left={`${stage.left}%`}
      style:top={`${stage.top}%`}
      style:width={`${(venueLayout.stage.width / width) * 100}%`}
      style:height={`${(venueLayout.stage.depth / depth) * 100}%`}
    >
      <strong class={["font-medium", "text-[13px]"]}>舞 台</strong>
      <span class={["text-[9px]", "tracking-[0.2em]"]}>STAGE</span>
    </div>
    <div
      class={["absolute", "-translate-x-1/2", "-translate-y-1/2", "flex", "items-center", "justify-center", "bg-(--muted)", "rounded-lg"]}
      aria-hidden="true"
      style:left={`${aisle.left}%`}
      style:top={`${aisle.top}%`}
      style:width={`${(venueLayout.aisle.width / width) * 100}%`}
      style:height={`${(venueLayout.aisle.depth / depth) * 100}%`}
    >
      <span
        class={["[writing-mode:vertical-rl]", "text-[10px]", "tracking-[0.3em]", "text-(--muted-foreground)"]}
      >
        中央过道
      </span>
    </div>
    {#each rows as seat (seat.row)}
      <span
        class={["absolute", "left-[3%]", "-translate-y-1/2", "text-[11px]", "text-(--muted-foreground)"]}
        style:top={`${projectSeatToPlan(seat).top}%`}
        >{seat.row}排</span
      >
    {/each}
    {#each props.seats as seat (seat.id)}
      {@const state = seatVisualState(
        seat.id,
        props.seatStates,
        props.selectedSeatIds,
      )}
      {@const position = projectSeatToPlan(seat)}
      <button
        type="button"
        class={["absolute", "-translate-x-1/2", "-translate-y-1/2", "w-[4.25%]", "h-[4.25%]", "rounded-t-[7px]", "rounded-b-[3px]", "text-[11px]", "font-semibold", "cursor-pointer", "[font-variant-numeric:tabular-nums]", "disabled:cursor-not-allowed", "enabled:hover:outline-2", "enabled:hover:outline-(--ring)", "enabled:hover:outline-offset-2", "focus-visible:outline-2", "focus-visible:outline-(--foreground)", "focus-visible:outline-offset-3", ...SEAT_STATE_CLASS[state]]}
        data-seat-id={seat.id}
        data-world-x={seat.x}
        data-world-y={seat.y}
        data-world-z={seat.z}
        style:left={`${position.left}%`}
        style:top={`${position.top}%`}
        aria-label={`${seat.label}，${SEAT_VISUAL_LABEL[state]}`}
        aria-pressed={state === "selected"}
        title={`${seat.label} · ${SEAT_VISUAL_LABEL[state]}`}
        disabled={props.disabled || state === "sold" || state === "unavailable"}
        onclick={() => props.onSeatToggle(seat.id)}
        onpointerenter={() => props.onSeatHover?.(seat.id)}
        onpointerleave={() => props.onSeatHover?.(null)}
        onfocus={() => props.onSeatHover?.(seat.id)}
        onblur={() => props.onSeatHover?.(null)}>{seat.number}</button
      >
    {/each}
    <p
      class={["absolute", "bottom-[1%]", "w-full", "text-center", "text-[11px]", "text-(--muted-foreground)"]}
    >
      入口 / 后排
    </p>
  </div>
</div>
