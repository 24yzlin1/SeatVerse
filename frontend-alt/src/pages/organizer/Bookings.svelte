<script lang="ts">
  import { toast } from "svelte-sonner";

  import { Badge } from "$lib/components/ui/badge";
  import * as Item from "$lib/components/ui/item";

  import Error from "@/common/Error.svelte";
  import Description from "@/pages/organizer/components/Description.svelte";
  import NavigationLayout from "@/layout/NavigationLayout.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Page, RosterEntry } from "@/common/api";
  import { BOOKING_STATUS_LABEL } from "@/common/utils/groupBookings";
  import { formatDateTime } from "@/common/utils/datetime";

  const { params }: { params: Record<string, string> } = $props();

  // The route parameter is the event id whose roster is displayed.
  const eventId = $derived(
    /^[1-9]\d*$/.test(params.id ?? "") ? Number(params.id) : Number.NaN,
  );

  let error = $state("");
  let loaded = $state(false);
  let rosterEntries: RosterEntry[] = $state([]);

  async function loadBookings(currentEventId: number) {
    try {
      const page = await request<Page<RosterEntry>>(
        `${endpoints.eventBookings(currentEventId)}?page=1&pageSize=100`,
      );
      rosterEntries = page.items;
    } catch (requestError: unknown) {
      error =
        requestError instanceof ApiError
          ? requestError.message
          : "获取活动名单失败";
    } finally {
      loaded = true;
    }
  }

  // Reload the roster whenever the route event id changes.
  $effect(() => {
    const currentId = eventId;
    if (!Number.isSafeInteger(currentId)) {
      return;
    }
    void loadBookings(currentId);
  });

  $effect(() => {
    if (error.length === 0) {
      return;
    }

    toast.error(error);
    error = "";
  });
</script>

<NavigationLayout {panel} {body} />

{#snippet panel()}
  <Description category="bookings" />
{/snippet}

{#snippet body()}
  {#if !Number.isSafeInteger(eventId)}
    <Error description="无效的活动 ID" />
  {:else}
    <div class={["px-2", "flex", "flex-col"]}>
      {#if !loaded}
        <!-- TODO: show a skeleton placeholder while the event roster is loading. -->
      {:else}
        {#each rosterEntries as rosterEntry (rosterEntry.id)}
          <Item.Root>
            <Item.Content class={["overflow-hidden"]}>
              <Item.Title class={["line-clamp-1"]}>
                {rosterEntry.user.name}
              </Item.Title>
              <Item.Description class={["line-clamp-1"]}>
                {rosterEntry.seats.map((seat) => seat.label).join("、")} · 预约于
                {formatDateTime(rosterEntry.createdAt)}
              </Item.Description>
              <div class={["flex", "gap-2"]}>
                <Badge
                  variant={rosterEntry.status === "cancelled"
                    ? "destructive"
                    : "default"}
                >
                  {BOOKING_STATUS_LABEL[rosterEntry.status]}
                </Badge>
              </div>
            </Item.Content>
          </Item.Root>
        {/each}
      {/if}
    </div>
  {/if}
{/snippet}
