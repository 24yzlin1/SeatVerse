<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import { formatDateTime } from "@/common/utils/datetime";
  import {
    deriveEventDisplayStatus,
    EVENT_SHORT_STATUS_LABEL,
  } from "@/common/utils/labels";
  import type { SeatMapData } from "@/pages/seatmap/types";

  const { event, now }: { event: SeatMapData["event"]; now: number } = $props();
  const status = $derived(deriveEventDisplayStatus(event, now));
</script>

<section aria-label="本场活动" class="flex flex-col gap-2">
  <div class="flex flex-wrap items-center gap-2">
    <h1 class="text-lg font-medium break-words">{event.title}</h1>
    <Badge variant={status === "published" ? "default" : "secondary"}>
      {EVENT_SHORT_STATUS_LABEL[status]}
    </Badge>
  </div>
  <p class="text-sm text-muted-foreground">{event.venue.name}</p>
  <p class="text-sm text-muted-foreground">
    <time datetime={event.startTime}>{formatDateTime(event.startTime)}</time>
    <span aria-label="至"> — </span>
    <time datetime={event.endTime}>{formatDateTime(event.endTime)}</time>
  </p>
</section>
