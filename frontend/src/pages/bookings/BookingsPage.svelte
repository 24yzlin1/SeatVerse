<script lang="ts">
  import { onMount } from "svelte";

  import { ApiError } from "@/common/api";
  import type { Booking } from "@/common/api";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";

  import BookingCard from "./BookingCard.svelte";
  import { USE_MOCK_BOOKINGS, loadBookings } from "./bookings.load";

  type PageState = "loading" | "error" | "empty" | "success";

  let pageState = $state<PageState>("loading");
  let bookings = $state<Booking[]>([]);
  let total = $state(0);
  let errorMessage = $state("");

  async function load(): Promise<void> {
    pageState = "loading";
    errorMessage = "";
    try {
      const page = await loadBookings();
      bookings = page.items;
      total = page.total;
      pageState = page.items.length === 0 ? "empty" : "success";
    } catch (error) {
      errorMessage =
        error instanceof ApiError ? error.message : "加载预约失败，请稍后重试";
      pageState = "error";
    }
  }

  onMount(() => {
    void load();
  });
</script>

<section class="min-h-screen bg-background p-8">
  <div class="mx-auto w-full max-w-5xl">
    <header class="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-foreground">我的预约</h1>
        <p class="mt-2 text-muted-foreground">查看你已预约的活动与座位</p>
      </div>
      {#if USE_MOCK_BOOKINGS}
        <span
          class={[
            "shrink-0",
            "self-start",
            "rounded-full",
            "bg-muted",
            "px-3",
            "py-1",
            "text-xs",
            "font-medium",
            "text-muted-foreground",
          ]}
        >
          演示数据
        </span>
      {/if}
    </header>

    {#if pageState === "loading"}
      <div
        class={["grid", "grid-cols-1", "gap-4", "md:grid-cols-2"]}
        role="status"
        aria-label="正在加载预约"
        aria-live="polite"
      >
        {#each [0, 1, 2] as index (index)}
          <div class={["animate-pulse", "rounded-xl", "border", "border-border", "bg-card", "p-6"]}>
            <div class={["mb-4", "h-6", "w-2/3", "rounded", "bg-muted"]}></div>
            <div class={["mb-2", "h-4", "w-1/2", "rounded", "bg-muted"]}></div>
            <div class={["mb-2", "h-4", "w-2/3", "rounded", "bg-muted"]}></div>
            <div class={["h-4", "w-1/3", "rounded", "bg-muted"]}></div>
          </div>
        {/each}
      </div>
    {:else if pageState === "error"}
      <ErrorState message={errorMessage} />
      <div class={["flex", "justify-center"]}>
        <button
          type="button"
          onclick={load}
          class={[
            "rounded-md",
            "bg-primary",
            "px-4",
            "py-2",
            "text-sm",
            "font-medium",
            "text-primary-foreground",
            "transition-colors",
            "hover:bg-primary/90",
          ]}
        >
          重试
        </button>
      </div>
    {:else if pageState === "empty"}
      <Empty message="还没有预约" />
      <div class={["flex", "justify-center"]}>
        <a
          href="#/events"
          class={[
            "rounded-md",
            "bg-primary",
            "px-4",
            "py-2",
            "text-sm",
            "font-medium",
            "text-primary-foreground",
            "transition-colors",
            "hover:bg-primary/90",
          ]}
        >
          去看看活动
        </a>
      </div>
    {:else}
      <p class={["mb-4", "text-sm", "text-muted-foreground"]}>共 {total} 条预约</p>
      <ul class={["grid", "grid-cols-1", "gap-4", "md:grid-cols-2"]}>
        {#each bookings as booking (booking.id)}
          <li><BookingCard {booking} /></li>
        {/each}
      </ul>
    {/if}
  </div>
</section>
