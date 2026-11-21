<script lang="ts">
  import Error from "@/common/Error.svelte";
  import SeatBooking from "@/pages/seatmap/SeatBooking.svelte";

  const { params }: { params: Record<string, string> } = $props();

  // Derived exactly like EventDetail: a positive integer id, NaN otherwise.
  const eventId = $derived(
    /^[1-9]\d*$/.test(params.id ?? "") ? Number(params.id) : Number.NaN,
  );
</script>

{#if !Number.isSafeInteger(eventId)}
  <Error description="无效的活动 ID" />
{:else}
  <SeatBooking {eventId} />
{/if}
