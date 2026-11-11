<script lang="ts">
  import { request, ApiError } from "@/common/api";
  import type { EventSummary } from "@/common/api/types";
  import Loading from "@/common/components/Loading.svelte";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import { router } from "@/common/router";

  let { id }: { id: string } = $props();

  let pageState = $state<"loading" | "error" | "empty" | "success">("loading");
  let event = $state<EventSummary | null>(null);
  let errorMessage = $state("");

  async function fetchEventDetail() {
    pageState = "loading";
    errorMessage = "";

    try {
      const res = await request<EventSummary>(`/events/${id}`, {
        method: "GET"
      });

      if (!res) {
        pageState = "empty";
        return;
      }

      event = res;
      pageState = "success";
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        errorMessage = error.message;
      } else {
        errorMessage = "获取活动详情失败";
      }
      pageState = "error";
    }
  }

  function goToSeatMap() {
    if (event) {
      router.navigate(`/events/${event.id}/seats`);
    }
  }

  $effect(() => {
    fetchEventDetail();
  });
</script>

<div class={["min-h-screen", "bg-background", "p-8"]}>
  <div class={["max-w-3xl", "mx-auto"]}>
    
    <button 
      onclick={() => router.navigate("/events")}
      class={["text-sm", "text-muted-foreground", "hover:text-primary", "transition-colors", "mb-8", "inline-flex", "items-center", "gap-1"]}
    >
      ← 返回活动列表
    </button>

    {#if pageState === "loading"}
      <Loading />
    {:else if pageState === "error"}
      <ErrorState message={errorMessage} />
    {:else if pageState === "empty"}
      <Empty message="活动不存在或已下架" />
    {:else if pageState === "success" && event}
      
      <div class={["bg-card", "border", "border-border", "rounded-2xl", "p-8", "shadow-sm"]}>
        
        <div class={["flex", "justify-between", "items-start", "mb-6"]}>
          <h1 class={["text-3xl", "font-bold", "text-foreground"]}>{event.title}</h1>
          <span class={[
            "px-3", "py-1", "text-sm", "font-medium", "rounded-full",
            ...(event.status === "published" 
              ? ["bg-primary/10", "text-primary"] 
              : ["bg-muted", "text-muted-foreground"])
          ]}>
            {event.status === "published" ? "预约中" : "已结束"}
          </span>
        </div>

        <div class={["flex", "flex-col", "gap-4", "text-base", "text-muted-foreground", "mb-10"]}>
          <div class={["flex", "items-center", "gap-3"]}>
            <span class={["font-medium", "text-foreground", "w-20"]}>活动场馆</span>
            <span>📍 {event.venue.name}</span>
          </div>
          <div class={["flex", "items-center", "gap-3"]}>
            <span class={["font-medium", "text-foreground", "w-20"]}>开始时间</span>
            <span>🕒 {new Date(event.startTime).toLocaleString()}</span>
          </div>
          <div class={["flex", "items-center", "gap-3"]}>
            <span class={["font-medium", "text-foreground", "w-20"]}>结束时间</span>
            <span>🕒 {new Date(event.endTime).toLocaleString()}</span>
          </div>
        </div>

        <div class={["flex", "justify-end", "border-t", "border-border", "pt-6"]}>
          <button
            onclick={goToSeatMap}
            disabled={event.status !== "published"}
            class={[
              "inline-flex", "items-center", "justify-center", "rounded-md",
              "text-sm", "font-medium", "h-11", "px-8",
              "bg-primary", "text-primary-foreground", "hover:bg-primary/90",
              "disabled:pointer-events-none", "disabled:opacity-50"
            ]}
          >
            {event.status === "published" ? "进入 3D 选座" : "该活动已停止预约"}
          </button>
        </div>

      </div>
    {/if}
  </div>
</div>