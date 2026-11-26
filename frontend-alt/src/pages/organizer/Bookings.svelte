<script lang="ts">
  import { toast } from "svelte-sonner";
  import { RiGroupLine } from "remixicon-svelte";

  import { Badge } from "$lib/components/ui/badge";
  import * as Item from "$lib/components/ui/item";
  import * as Tabs from "$lib/components/ui/tabs";

  import Error from "@/common/Error.svelte";
  import VisualCard from "@/common/VisualCard.svelte";
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
  let requestVersion = 0;

  // Booking-status counts of this event (GET /events/{id}/roster-summary),
  // rendered as the participation chart on top; `null` keeps it hidden
  // until the server answers.
  let rosterSummary: {
    total: number;
    reserved: number;
    checkedIn: number;
    cancelled: number;
  } | null = $state(null);

  // Booking-status filter tabs for the roster; filtering happens server-side
  // via the `status` query param (backend-api-proposals.md §7).
  let rosterStatusFilter = $state("all");
  const rosterStatusFilters = [
    { value: "all", label: "全部" },
    { value: "reserved", label: "待参加" },
    { value: "used", label: "已核验" },
    { value: "cancelled", label: "已取消" },
  ] as const;

  function describeError(operationError: unknown, fallback: string): string {
    return operationError instanceof ApiError
      ? operationError.message
      : fallback;
  }

  async function loadBookings(currentEventId: number) {
    const version = ++requestVersion;
    try {
      const statusQuery =
        rosterStatusFilter === "all" ? "" : `&status=${rosterStatusFilter}`;
      const page = await request<Page<RosterEntry>>(
        `${endpoints.eventBookings(currentEventId)}?page=1&pageSize=100${statusQuery}`,
      );
      if (version !== requestVersion) {
        return;
      }
      rosterEntries = page.items;
      loaded = true;
    } catch (requestError: unknown) {
      if (version !== requestVersion) {
        return;
      }
      error = describeError(requestError, "获取活动名单失败");
      loaded = true;
    }
  }

  async function loadSummary(currentEventId: number) {
    try {
      rosterSummary = await request<{
        total: number;
        reserved: number;
        checkedIn: number;
        cancelled: number;
      }>(endpoints.eventRosterSummary(currentEventId));
    } catch {
      rosterSummary = null;
    }
  }

  // Reload the roster whenever the route event id or the status tab changes.
  $effect(() => {
    const currentId = eventId;
    const filter = rosterStatusFilter;
    if (!Number.isSafeInteger(currentId)) {
      return;
    }
    void loadBookings(currentId);
    void filter;
    return () => {
      requestVersion++;
    };
  });

  // The summary chart follows the event only.
  $effect(() => {
    const currentId = eventId;
    if (!Number.isSafeInteger(currentId)) {
      return;
    }
    void loadSummary(currentId);
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
    <div class={["px-6", "py-4"]}>
      {#if rosterSummary}
        <VisualCard
          type="pie"
          title="参与情况"
          icon={RiGroupLine}
          data={[
            { label: "待参加", value: rosterSummary.reserved },
            { label: "已核验", value: rosterSummary.checkedIn },
            { label: "已取消", value: rosterSummary.cancelled },
          ]}
          options={{
            note: rosterSummary.total,
            noteDescription: "总单数",
          }}
        />
      {:else}
        <p class={["text-sm", "text-muted-foreground"]}>参与情况暂不可用</p>
      {/if}
    </div>
    <div class={[
      "sticky",
      "top-14",
      "h-14",
      "px-6",
      "flex",
      "items-center",
      "gap-4",
      "bg-background/80",
      "backdrop-blur-xs",
    ]}>
      <div class={["grow", "overflow-x-scroll", "overflow-y-hidden"]}>
        <Tabs.Root bind:value={rosterStatusFilter} class={["w-full"]}>
          <Tabs.List>
            {#each rosterStatusFilters as option (option.value)}
              <Tabs.Trigger value={option.value}>
                {option.label}
              </Tabs.Trigger>
            {/each}
          </Tabs.List>
        </Tabs.Root>
      </div>
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
                {rosterEntry.seats
                  .map((seat) => seat.label)
                  .join("、")} · 预约于 {formatDateTime(rosterEntry.createdAt)}
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
