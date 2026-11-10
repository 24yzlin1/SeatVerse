<script lang="ts">
  import { navigate, router } from "@/common/router";
  import SeatSelectionPage from "./SeatSelectionPage.svelte";
  import type { EventId } from "./types";

  const rawId = $derived(router.params.id ?? "");
  const eventId = $derived(
    /^[1-9]\d*$/.test(rawId) && Number.isSafeInteger(Number(rawId))
      ? Number(rawId)
      : Number.NaN,
  );

  function changeEvent(id: EventId): void {
    navigate(`/events/${encodeURIComponent(String(id))}/seats`);
  }
</script>

<SeatSelectionPage {eventId} onEventChange={changeEvent} />
