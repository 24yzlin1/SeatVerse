<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { push } from "svelte-spa-router";
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
  import { loadSeatStatistics } from "@/pages/seatmap/api";
  import { loadBookingWindow } from "@/pages/bookings/api";
  import { Button } from "$lib/components/ui/button";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Booking, EventRecord } from "@/common/api";
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
  let bookingPage = $state(0);
  let bookingTotal = $state(0);
  let bookingLoading = $state(false);
  let bookingError = $state("");
  let bookingVersion = 0;
  let statisticsVersion = 0;

  // Participation summary computed from the seat states of this event;
  // `null` means the seat data has not loaded (the chart stays hidden).
  let seatStats: { sold: number; locked: number; available: number } | null =
    $state(null);

  let selectedOption = $state("0");

  let now = $state(Date.now());

  async function loadDetail(currentId: number, signal: AbortSignal) {
    try {
      const result = await request<EventRecord>(
        endpoints.eventDetail(currentId),
        { signal },
      );
      if (currentId === eventId && !signal.aborted) {
        detail = result;
      }
    } catch (requestError: unknown) {
      if (currentId !== eventId || signal.aborted) {
        return;
      }
      error =
        requestError instanceof ApiError
          ? requestError.message
          : "获取活动详情失败";
    }
  }

  async function loadSeatStats(currentId: number) {
    const version = ++statisticsVersion;
    try {
      const result = await loadSeatStatistics(currentId);
      if (currentId === eventId && version === statisticsVersion) {
        seatStats = result;
      }
    } catch {
      if (currentId === eventId && version === statisticsVersion) {
        seatStats = null;
      }
    }
  }

  async function loadBookings(currentId: number, page = 1) {
    const version = ++bookingVersion;
    const userId = authentication.user?.id;
    bookingLoading = true;
    bookingError = "";
    try {
      const result = await loadBookingWindow({ eventId: currentId }, page);
      if (
        version !== bookingVersion ||
        currentId !== eventId ||
        userId !== authentication.user?.id
      ) {
        return;
      }
      eventBookings = result.items;
      bookingPage = result.page;
      bookingTotal = result.total;
    } catch (requestError: unknown) {
      if (
        version === bookingVersion &&
        currentId === eventId &&
        userId === authentication.user?.id
      ) {
        bookingError =
          requestError instanceof ApiError
            ? requestError.message
            : "预约列表没能更新，稍后再试试";
      }
    } finally {
      if (version === bookingVersion) {
        bookingLoading = false;
      }
    }
  }

  // Reload the detail whenever the route id changes.
  $effect(() => {
    const currentId = eventId;
    const controller = new AbortController();
    detail = null;
    error = "";
    seatStats = null;
    if (!Number.isSafeInteger(currentId)) {
      error = "无效的活动 ID";
      return;
    }
    untrack(() => {
      void loadDetail(currentId, controller.signal);
      void loadSeatStats(currentId);
    });
    return () => {
      controller.abort();
      statisticsVersion++;
    };
  });

  // The booking tab requires a session; load the list as soon as one exists.
  $effect(() => {
    const currentId = eventId;
    const loggedIn = authentication.isLoggedIn;
    const userId = authentication.user?.id;
    untrack(() => {
      eventBookings = null;
      bookingPage = 0;
      bookingTotal = 0;
      bookingError = "";
      bookingLoading = false;
      if (Number.isSafeInteger(currentId) && loggedIn && userId !== undefined) {
        void loadBookings(currentId);
      }
    });
    return () => {
      bookingVersion++;
    };
  });

  onMount(() => {
    const update = () => {
      now = Date.now();
      // Keep bookings and seat availability fresh on long-lived visits; the
      // seat tab has its own poller inside the SeatBooking container.
      if (authentication.isLoggedIn && !bookingLoading) {
        void loadBookings(eventId, Math.max(1, bookingPage));
      }
      void loadSeatStats(eventId);
    };
    const timer = window.setInterval(update, 30000);
    window.addEventListener("seatverse:booking-created", update);
    window.addEventListener("seatverse:booking-cancelled", update);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("seatverse:booking-created", update);
      window.removeEventListener("seatverse:booking-cancelled", update);
    };
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
          {#each tabOptions as x, i (x)}
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
        <p class="px-4 py-6">请通过右上角账户入口登录后查看本场预约。</p>
      {:else if !eventBookings}
        <p class="px-4 py-6" role="status">
          {bookingError || "正在加载本场预约…"}
        </p>
      {:else if eventBookings.length === 0}
        <p class="px-4 py-6">暂无本场预约。</p>
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
      {#if authentication.isLoggedIn && bookingError}
        <p class="px-4 text-destructive" role="alert">{bookingError}</p>
        <Button
          variant="secondary"
          disabled={bookingLoading}
          onclick={() => {
            void loadBookings(eventId, bookingPage + 1);
          }}>重试加载预约</Button
        >
      {:else if eventBookings && eventBookings.length < bookingTotal}
        <Button
          variant="secondary"
          disabled={bookingLoading}
          onclick={() => {
            void loadBookings(eventId, bookingPage + 1);
          }}>{bookingLoading ? "加载中…" : "加载更多预约"}</Button
        >
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
