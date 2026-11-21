<script lang="ts">
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { toast } from "svelte-sonner";

  import { Badge } from "$lib/components/ui/badge";
  import * as Item from "$lib/components/ui/item";
  import * as Tabs from "$lib/components/ui/tabs";

  import Description from "@/pages/bookings/components/Description.svelte";
  import NavigationLayout from "@/layout/NavigationLayout.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Booking, Page } from "@/common/api";
  import { BOOKING_STATUS_LABEL } from "@/common/utils/groupBookings";

  let error = $state("");

  let bookings: Booking[] = $state([]);

  // Status filter tabs; "all" shows every booking of the current user.
  let statusFilter = $state("all");

  const statusFilters = [
    { value: "all", label: "全部" },
    { value: "reserved", label: "待参加" },
    { value: "used", label: "已签到" },
    { value: "cancelled", label: "已取消" },
  ] as const;

  const visibleBookings = $derived(
    statusFilter === "all"
      ? bookings
      : bookings.filter((booking) => booking.status === statusFilter),
  );

  async function loadBookings() {
    try {
      const page = await request<Page<Booking>>(
        `${endpoints.bookingsMe()}?page=1&pageSize=100`,
      );
      bookings = page.items;
    } catch (requestError: unknown) {
      error =
        requestError instanceof ApiError
          ? requestError.message
          : "获取预约列表失败";
    }
  }

  onMount(loadBookings);

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
          {#each statusFilters as option}
            <Tabs.Trigger value={option.value}>{option.label}</Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>
    </div>
  </div>
  <div class={["px-2", "flex", "flex-col"]}>
    {#each visibleBookings as booking (booking.id)}
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
      </Item.Root>
    {/each}
  </div>
{/snippet}
