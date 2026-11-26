<script lang="ts">
  import { untrack } from "svelte";
  import { push } from "svelte-spa-router";
  import { toast } from "svelte-sonner";

  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import * as Item from "$lib/components/ui/item";
  import * as Tabs from "$lib/components/ui/tabs";

  import Description from "@/pages/events/components/Description.svelte";
  import NavigationLayout from "@/layout/NavigationLayout.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { EventSummary, Page } from "@/common/api";
  import {
    deriveEventDisplayStatus,
    EVENT_SHORT_STATUS_LABEL,
  } from "@/common/utils/labels";
  import { formatDateTime } from "@/common/utils/datetime";

  let error = $state("");

  let events: EventSummary[] = $state([]);
  let loaded = $state(false);
  let requestVersion = 0;

  // Status filter tabs; filtering happens server-side via the `status` /
  // `ended` query params (see backend-api-proposals.md §1). "ended" is a
  // display-only state the API exposes through `ended=true`.
  let statusFilter = $state("all");
  const now = $state(Date.now());

  const statusFilters = [
    { value: "all", label: "全部" },
    { value: "published", label: "预约中" },
    { value: "closed", label: "已停约" },
    { value: "ended", label: "已结束" },
    { value: "cancelled", label: "已取消" },
  ] as const;

  function filterQuery(filter: string): string {
    switch (filter) {
      case "published":
        return "&status=published";
      case "closed":
        return "&status=closed";
      case "ended":
        return "&ended=true";
      case "cancelled":
        return "&status=cancelled";
      default:
        return "";
    }
  }

  async function loadEvents() {
    const version = ++requestVersion;
    try {
      const page = await request<Page<EventSummary>>(
        `${endpoints.events()}?page=1&pageSize=100${filterQuery(statusFilter)}`,
      );
      if (version !== requestVersion) {
        return;
      }
      events = page.items;
      loaded = true;
    } catch (requestError: unknown) {
      if (version !== requestVersion) {
        return;
      }
      error =
        requestError instanceof ApiError
          ? requestError.message
          : "获取活动列表失败";
      loaded = true;
    }
  }

  // Reload from the API whenever the status tab changes.
  $effect(() => {
    const filter = statusFilter;
    untrack(() => {
      void loadEvents();
    });
    void filter;
    return () => {
      requestVersion++;
    };
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
  <Description category="event" />
{/snippet}

{#snippet body()}
  <div
    class={[
      "sticky",
      "top-14",
      "h-14",
      "px-6",
      "flex",
      "items-center",
      "gap-4",
      "bg-background/80",
      "backdrop-blur-xs",
    ]}
  >
    <div class={["grow", "overflow-x-scroll", "overflow-y-hidden"]}>
      <Tabs.Root bind:value={statusFilter} class={["w-full"]}>
        <Tabs.List>
          {#each statusFilters as option (option.value)}
            <Tabs.Trigger value={option.value}>{option.label}</Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>
    </div>
  </div>
  <div class={["px-2", "flex", "flex-col"]}>
    {#if !loaded}
      <!-- Blank while the list loads; the rows replace this branch once ready. -->
    {:else}
      {#each events as x (x.id)}
        {@const displayStatus = deriveEventDisplayStatus(x, now)}
        <Item.Root
          class={["click-link"]}
          onclick={() => push(`/events/${x.id}`)}
        >
          <Item.Media class={["size-8"]}>
            <Avatar.Root class={["rounded-lg"]}>
              <Avatar.Fallback>
                {x.title.charAt(0)}
              </Avatar.Fallback>
            </Avatar.Root>
          </Item.Media>
          <Item.Content class={["overflow-hidden"]}>
            <Item.Title class={["line-clamp-1"]}>
              {x.title}
            </Item.Title>
            <div class={["flex", "gap-2"]}>
              <Badge
                variant={displayStatus === "published"
                  ? "default"
                  : "destructive"}
              >
                {EVENT_SHORT_STATUS_LABEL[displayStatus]}
              </Badge>
              <Item.Description class={["line-clamp-1"]}>
                {formatDateTime(x.startTime)} — {formatDateTime(x.endTime)}
              </Item.Description>
            </div>
          </Item.Content>
        </Item.Root>
      {/each}
    {/if}
  </div>
{/snippet}
