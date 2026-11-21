<script lang="ts">
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { toast } from "svelte-sonner";
  import {
    RiCalendarLine,
    RiFlagLine,
    RiGroupLine,
    RiMapPinLine,
    RiUserLine,
  } from "remixicon-svelte";

  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import * as Item from "$lib/components/ui/item";
  import * as Tabs from "$lib/components/ui/tabs";

  import Error from "@/common/Error.svelte";
  import VisualCard from "@/common/VisualCard.svelte";
  import SeatBooking from "@/pages/seatmap/SeatBooking.svelte";
  import { loadSeatMap } from "@/pages/seatmap/api";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Booking, EventRecord, Page } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { BOOKING_STATUS_LABEL } from "@/common/utils/groupBookings";
  import {
    deriveEventDisplayStatus,
    EVENT_SHORT_STATUS_LABEL,
  } from "@/common/utils/labels";
  import { formatDateTime } from "@/common/utils/datetime";

  const { params }: { params: Record<string, string> } = $props();

  const eventId = $derived(
    /^[1-9]\d*$/.test(params.id ?? "") ? Number(params.id) : Number.NaN,
  );

  let error = $state("");

  let detail: EventRecord | null = $state(null);
  let eventBookings: Booking[] | null = $state(null);

  // Participation summary computed from the seat states of this event;
  // `null` means the seat data has not loaded (the chart stays hidden).
  let seatStats: { sold: number; locked: number; available: number } | null =
    $state(null);

  let selectedOption = $state("0");

  let now = $state(Date.now());

  async function loadDetail(currentId: number) {
    try {
      detail = await request<EventRecord>(endpoints.eventDetail(currentId));
    } catch (requestError: unknown) {
      error =
        requestError instanceof ApiError
          ? requestError.message
          : "获取活动详情失败";
    }
  }

  async function loadSeatStats(currentId: number) {
    try {
      const seatMap = await loadSeatMap(currentId);
      const sold = seatMap.seats.filter(
        (seat) => seatMap.seatStates.get(seat.id) === "sold",
      ).length;
      const locked = seatMap.seats.filter(
        (seat) => seatMap.seatStates.get(seat.id) === "locked",
      ).length;
      const available = seatMap.seats.filter(
        (seat) => seatMap.seatStates.get(seat.id) === "available",
      ).length;
      seatStats = { sold, locked, available };
    } catch {
      seatStats = null;
    }
  }

  async function loadBookings(currentId: number) {
    try {
      const page = await request<Page<Booking>>(
        `${endpoints.bookingsMe()}?page=1&pageSize=100`,
      );
      eventBookings = page.items.filter(
        (booking) => booking.event.id === currentId,
      );
    } catch (requestError: unknown) {
      // Booking list failures are not fatal; keep the stale list and report
      // through a toast instead of replacing the whole tab.
      toast.error(
        requestError instanceof ApiError
          ? requestError.message
          : "预约列表没能更新，稍后再试试",
      );
    }
  }

  // Reload the detail whenever the route id changes.
  $effect(() => {
    const currentId = eventId;
    if (!Number.isSafeInteger(currentId)) {
      error = "无效的活动 ID";
      return;
    }
    void loadDetail(currentId);
    void loadSeatStats(currentId);
  });

  // The booking tab requires a session; load the list as soon as one exists.
  $effect(() => {
    const currentId = eventId;
    if (
      Number.isSafeInteger(currentId) &&
      authentication.isLoggedIn &&
      eventBookings === null
    ) {
      void loadBookings(currentId);
    }
  });

  onMount(() => {
    const timer = window.setInterval(() => {
      now = Date.now();
      // Keep bookings and seat availability fresh on long-lived visits; the
      // seat tab has its own poller inside the SeatBooking container.
      if (authentication.isLoggedIn) {
        void loadBookings(eventId);
      }
      void loadSeatStats(eventId);
    }, 30000);
    return () => window.clearInterval(timer);
  });
</script>

{#if error.length !== 0}
  <Error
    title="活动不见了"
    description={error}
    backCallback={() => push("/events")}
  />
{:else if !detail}
  <!-- TODO: show a skeleton placeholder while the event detail is loading. -->
{:else}
  {@render introduction()}
  <div
    class={[
      "z-9",
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
      <Tabs.Root bind:value={selectedOption} class={["w-full"]}>
        <Tabs.List>
          {@const tabOptions = ["详情", "我的预约", "立即选座"]}
          {#each tabOptions as x, i}
            <Tabs.Trigger value={i.toString()}>{x}</Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>
    </div>
  </div>

  {#if selectedOption === "0"}
    <div class={["px-6", "py-4", "flex", "flex-col", "gap-4"]}>
      <p
        class={[
          "text-sm",
          "leading-7",
          "text-muted-foreground",
          "whitespace-pre-line",
        ]}
      >
        {detail.description}
      </p>
      {#if seatStats}
        <VisualCard
          type="pie"
          title="参与情况"
          icon={RiGroupLine}
          data={[
            { label: "已预约", value: seatStats.sold },
            { label: "已锁定", value: seatStats.locked },
            { label: "空位", value: seatStats.available },
          ]}
          options={{ note: seatStats.sold, noteDescription: "已预约座位" }}
        />
      {/if}
    </div>
  {/if}
  {#if selectedOption === "1"}
    <div class={["px-2", "flex", "flex-col"]}>
      {#if !authentication.isLoggedIn}
        <!-- TODO: show a sign-in prompt when the user is not logged in. -->
      {:else if !eventBookings}
        <!-- TODO: show a skeleton placeholder while bookings are loading. -->
      {:else if eventBookings.length === 0}
        <!-- TODO: show an empty state when there are no bookings. -->
      {:else}
        {#each eventBookings as booking (booking.id)}
          <Item.Root
            class={["click-link"]}
            onclick={() => push(`/bookings/${booking.id}/ticket`)}
          >
            <Item.Content class={["overflow-hidden"]}>
              <Item.Title class={["line-clamp-1"]}>
                {booking.seats.map((seat) => seat.label).join("、")}
              </Item.Title>
              <div class={["flex", "gap-2"]}>
                <Badge
                  variant={booking.status === "cancelled"
                    ? "destructive"
                    : "default"}
                >
                  {BOOKING_STATUS_LABEL[booking.status]}
                </Badge>
              </div>
            </Item.Content>
          </Item.Root>
        {/each}
      {/if}
    </div>
  {/if}
  {#if selectedOption === "2"}
    <SeatBooking {eventId} />
  {/if}
{/if}

{#snippet introduction()}
  <div class={["pt-4", "px-6"]}>
    <Item.Root variant="muted" class={["flex-nowrap", "overflow-hidden"]}>
      <Item.Media variant="image">
        <Avatar.Root size="lg">
          <Avatar.Fallback>
            {detail?.title.charAt(0)}
          </Avatar.Fallback>
        </Avatar.Root>
      </Item.Media>
      <Item.Content>
        <Item.Title>{detail?.title}</Item.Title>
        <div class={["flex", "gap-2"]}>
          {#if detail}
            {@const displayStatus = deriveEventDisplayStatus(detail, now)}
            <Badge
              variant={displayStatus === "published"
                ? "default"
                : "destructive"}
            >
              {EVENT_SHORT_STATUS_LABEL[displayStatus]}
            </Badge>
          {/if}
        </div>
      </Item.Content>
    </Item.Root>
    <div class={["py-4", "flex", "flex-col", "gap-2"]}>
      <Item.Root class={["p-0"]}>
        <Item.Media class={["size-8"]} variant="icon">
          <RiMapPinLine />
        </Item.Media>
        <Item.Content>
          <Item.Title>{detail?.venue.name}</Item.Title>
        </Item.Content>
      </Item.Root>
      <Item.Root class={["p-0"]}>
        <Item.Media class={["size-8"]} variant="icon">
          <RiCalendarLine />
        </Item.Media>
        <Item.Content>
          <Item.Title>
            {detail ? formatDateTime(detail.startTime) : ""}
          </Item.Title>
        </Item.Content>
      </Item.Root>
      <Item.Root class={["p-0"]}>
        <Item.Media class={["size-8"]} variant="icon">
          <RiFlagLine />
        </Item.Media>
        <Item.Content>
          <Item.Title>
            {detail ? formatDateTime(detail.endTime) : ""}
          </Item.Title>
        </Item.Content>
      </Item.Root>
      <Item.Root class={["p-0"]}>
        <Item.Media class={["size-8"]} variant="icon">
          <RiUserLine />
        </Item.Media>
        <Item.Content>
          <Item.Title>{detail?.organizerName}</Item.Title>
        </Item.Content>
      </Item.Root>
    </div>
  </div>
{/snippet}
