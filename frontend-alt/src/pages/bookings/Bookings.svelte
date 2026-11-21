<script lang="ts">
  import { untrack } from "svelte";
  import { push } from "svelte-spa-router";
  import { toast } from "svelte-sonner";
  import {
    RiCloseCircleLine,
    RiLoader4Line,
  } from "remixicon-svelte";

  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Item from "$lib/components/ui/item";
  import * as Tabs from "$lib/components/ui/tabs";

  import Description from "@/pages/bookings/components/Description.svelte";
  import NavigationLayout from "@/layout/NavigationLayout.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Booking, BookingStatus } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { loadBookingWindow } from "./api";
  import { BOOKING_STATUS_LABEL } from "@/common/utils/groupBookings";

  let error = $state("");

  let bookings: Booking[] = $state([]);
  let page = $state(0);
  let total = $state(0);
  let loading = $state(false);
  let cancelling = $state<number | null>(null);
  let requestVersion = 0;
  let errorReported = false;

  // Status filter tabs; "all" shows every booking of the current user.
  let statusFilter = $state("all");

  const statusFilters = [
    { value: "all", label: "全部" },
    { value: "reserved", label: "待参加" },
    { value: "used", label: "已签到" },
    { value: "cancelled", label: "已取消" },
  ] as const;

  async function loadBookings(nextPage = 1) {
    const version = ++requestVersion;
    const userId = authentication.user?.id;
    const status: BookingStatus | undefined =
      statusFilter === "reserved" ||
      statusFilter === "used" ||
      statusFilter === "cancelled"
        ? statusFilter
        : undefined;
    loading = true;
    error = "";
    try {
      const result = await loadBookingWindow({ status }, nextPage);
      if (version !== requestVersion || userId !== authentication.user?.id) {
        return;
      }
      bookings = result.items;
      page = result.page;
      total = result.total;
      errorReported = false;
    } catch (requestError: unknown) {
      if (version === requestVersion && userId === authentication.user?.id) {
        error =
          requestError instanceof ApiError
            ? requestError.message
            : "获取预约列表失败";
        // List failures surface as a toast instead of an inline error block.
        if (!errorReported) {
          errorReported = true;
          toast.error(error);
        }
      }
    } finally {
      if (version === requestVersion) {
        loading = false;
      }
    }
  }

  async function cancelBooking(booking: Booking) {
    if (cancelling !== null) {
      return;
    }
    cancelling = booking.id;
    const userId = authentication.user?.id;
    try {
      await request(endpoints.bookingCancel(booking.id), { method: "POST" });
      if (userId !== authentication.user?.id) {
        return;
      }
      window.dispatchEvent(
        new CustomEvent("seatverse:booking-cancelled", {
          detail: {
            bookingId: booking.id,
            eventId: booking.event.id,
            seatIds: booking.seats.map((seat) => seat.id),
          },
        }),
      );
      toast.success("预约已取消，座位已释放");
      await loadBookings();
    } catch (requestError: unknown) {
      toast.error(
        requestError instanceof Error
          ? requestError.message
          : "取消结果未能确认，请刷新预约核对",
      );
      if (userId === authentication.user?.id) {
        await loadBookings();
      }
    } finally {
      cancelling = null;
    }
  }

  $effect(() => {
    const filter = statusFilter;
    const userId = authentication.user?.id;
    untrack(() => {
      bookings = [];
      page = 0;
      total = 0;
      if (userId !== undefined) {
        void loadBookings();
      }
    });
    void filter;
    return () => {
      requestVersion++;
    };
  });
</script>

<NavigationLayout {panel} {body} />

{#snippet panel()}
  <Description category="booking" />
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
    {#each bookings as booking (booking.id)}
      <Item.Root
        class={["click-link"]}
        onclick={() => push(`/bookings/${booking.id}/ticket`)}
      >
        <Item.Content class={["overflow-hidden"]}>
          <Item.Title class={["line-clamp-1"]}>
            {booking.event.title}
          </Item.Title>
          <div class={["flex", "gap-2"]}>
            <Badge
              variant={booking.status === "cancelled"
                ? "destructive"
                : "default"}
            >
              {BOOKING_STATUS_LABEL[booking.status]}
            </Badge>
            <Item.Description class={["line-clamp-1"]}>
              {booking.seats.map((seat) => seat.label).join("、")}
            </Item.Description>
          </div>
        </Item.Content>
        {#if booking.status === "reserved" && Date.now() < Date.parse(booking.event.startTime)}
          <Button
            variant="secondary"
            size="icon"
            aria-label="取消预约"
            title="取消预约"
            disabled={cancelling !== null}
            onclick={(event) => {
              event.stopPropagation();
              void cancelBooking(booking);
            }}
          >
            {#if cancelling === booking.id}
              <RiLoader4Line class="animate-spin" />
            {:else}
              <RiCloseCircleLine />
            {/if}
          </Button>
        {/if}
      </Item.Root>
    {/each}
    {#if bookings.length < total && !error}
      <Button
        variant="secondary"
        disabled={loading}
        onclick={() => {
          void loadBookings(page + 1);
        }}>加载更多预约</Button
      >
    {/if}
  </div>
{/snippet}
