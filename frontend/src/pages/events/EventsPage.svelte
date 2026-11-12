<script lang="ts">
  import { SvelteURLSearchParams } from "svelte/reactivity";
  import { request, ApiError } from "@/common/api";
  import type { Page, EventSummary } from "@/common/api/types";
  import Loading from "@/common/components/Loading.svelte";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";

  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";

  let pageState = $state<"loading" | "error" | "empty" | "success">("loading");
  let events = $state<EventSummary[]>([]);
  let errorMessage = $state("");
  
  let keyword = $state("");
  let currentPage = $state(1);
  const pageSize = 10;

  async function fetchEvents() {
    pageState = "loading";
    errorMessage = "";
    
    try {
      const query = new SvelteURLSearchParams({
        page: currentPage.toString(),
        pageSize: pageSize.toString(),
      });
      if (keyword.trim()) query.append("keyword", keyword.trim());

      const res = await request<Page<EventSummary>>(`/events?${query.toString()}`, { method: "GET" });

      events = res.items;
      pageState = events.length === 0 ? "empty" : "success";
    } catch (error: unknown) {
      errorMessage = error instanceof ApiError ? error.message : "获取活动列表失败";
      pageState = "error";
    }
  }

  function handleSearch(e: SubmitEvent) {
    e.preventDefault();
    currentPage = 1;
    fetchEvents();
  }

  $effect(() => {
    fetchEvents();
  });
</script>

<div class={["min-h-screen", "bg-background", "p-8"]}>
  <div class={["max-w-5xl", "mx-auto"]}>
    
    <!-- 头部搜索区 -->
    <div class={["flex", "flex-col", "md:flex-row", "md:items-center", "justify-between", "mb-8", "gap-4"]}>
      <div>
        <h1 class={["text-3xl", "font-bold", "text-foreground"]}>发现活动</h1>
        <p class={["text-muted-foreground", "mt-2"]}>浏览并预约你感兴趣的校园活动</p>
      </div>

      <form onsubmit={handleSearch} class={["flex", "items-center", "gap-2"]}>
        <Input type="text" bind:value={keyword} placeholder="搜索活动名称..." class={["w-64"]} />
        <Button type="submit">搜索</Button>
      </form>
    </div>

    <!-- 列表区 -->
    <div class={["mt-8"]}>
      {#if pageState === "loading"}
        <Loading />
      {:else if pageState === "error"}
        <ErrorState message={errorMessage} />
      {:else if pageState === "empty"}
        <Empty message="没有找到相关活动" />
      {:else if pageState === "success"}
        <div class={["grid", "grid-cols-1", "md:grid-cols-2", "gap-6"]}>
          {#each events as event (event.id)}
            <a
              href={`#/events/${event.id}`}
              class={["p-6", "border", "border-border", "rounded-xl", "bg-card", "hover:shadow-md", "cursor-pointer"]}
            >
              <h2 class={["text-xl", "font-semibold"]}>{event.title}</h2>
              <p class={["text-sm", "text-muted-foreground", "mt-2"]}>📍 {event.venue.name}</p>
            </a>
          {/each}
        </div>
      {/if}
    </div>

  </div>
</div>
