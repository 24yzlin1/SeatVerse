<script lang="ts">
  import { request, ApiError } from "@/common/api";
  import type { Page, EventSummary } from "@/common/api/types";
  import Loading from "@/common/components/Loading.svelte";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import { router } from "@/common/router";

  let pageState = $state<"loading" | "error" | "empty" | "success">("loading");
  let events = $state<EventSummary[]>([]);
  let errorMessage = $state("");
  
  let keyword = $state("");
  let currentPage = $state(1);
  let totalPages = $state(1);
  let pageSize = 10;

  async function fetchEvents() {
    pageState = "loading";
    errorMessage = "";
    
    try {
      const query = new URLSearchParams({
        page: currentPage.toString(),
        pageSize: pageSize.toString(),
      });
      if (keyword.trim()) {
        query.append("keyword", keyword.trim());
      }

      const res = await request<Page<EventSummary>>(`/events?${query.toString()}`, {
        method: "GET"
      });

      events = res.items;
      totalPages = Math.ceil(res.total / res.pageSize) || 1;
      
      if (events.length === 0) {
        pageState = "empty";
      } else {
        pageState = "success";
      }
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        errorMessage = error.message;
      } else {
        errorMessage = "获取活动列表失败，请稍后重试";
      }
      pageState = "error";
    }
  }

  function handleSearch(e: SubmitEvent) {
    e.preventDefault();
    currentPage = 1;
    fetchEvents();
  }

  function handlePrevPage() {
    if (currentPage > 1) {
      currentPage -= 1;
      fetchEvents();
    }
  }

  function handleNextPage() {
    if (currentPage < totalPages) {
      currentPage += 1;
      fetchEvents();
    }
  }

  function goToDetail(id: number) {
    router.navigate(`/events/${id}`);
  }

  $effect(() => {
    fetchEvents();
  });
</script>

<div class={["min-h-screen", "bg-background", "p-8"]}>
  <div class={["max-w-5xl", "mx-auto"]}>
    
    <div class={["flex", "flex-col", "md:flex-row", "md:items-center", "justify-between", "mb-8", "gap-4"]}>
      <div>
        <h1 class={["text-3xl", "font-bold", "text-foreground"]}>发现活动</h1>
        <p class={["text-muted-foreground", "mt-2"]}>浏览并预约你感兴趣的校园活动</p>
      </div>

      <form onsubmit={handleSearch} class={["flex", "items-center", "gap-2"]}>
        <input
          type="text"
          bind:value={keyword}
          placeholder="搜索活动名称..."
          class={[
            "flex", "h-10", "w-64", "rounded-md", "border", "border-input",
            "bg-transparent", "px-3", "py-2", "text-sm", "text-foreground",
            "focus-visible:outline-none", "focus-visible:ring-2", "focus-visible:ring-ring"
          ]}
        />
        <button
          type="submit"
          class={[
            "inline-flex", "items-center", "justify-center", "rounded-md",
            "text-sm", "font-medium", "h-10", "px-4", "py-2",
            "bg-primary", "text-primary-foreground", "hover:bg-primary/90"
          ]}
        >
          搜索
        </button>
      </form>
    </div>

    <div class={["mt-8"]}>
      {#if pageState === "loading"}
        <Loading />
      {:else if pageState === "error"}
        <ErrorState message={errorMessage} />
        <div class={["flex", "justify-center", "mt-4"]}>
          <button
            onclick={fetchEvents}
            class={["text-sm", "text-primary", "hover:underline"]}
          >
            点击重试
          </button>
        </div>
      {:else if pageState === "empty"}
        <Empty message="没有找到相关活动" />
      {:else if pageState === "success"}
        <div class={["grid", "grid-cols-1", "md:grid-cols-2", "gap-6"]}>
          {#each events as event (event.id)}
            <div 
              onclick={() => goToDetail(event.id)}
              class={[
                "p-6", "border", "border-border", "rounded-xl", "bg-card",
                "hover:shadow-md", "transition-shadow", "cursor-pointer", "flex", "flex-col", "justify-between"
              ]}
            >
              <div>
                <div class={["flex", "justify-between", "items-start", "mb-4"]}>
                  <h2 class={["text-xl", "font-semibold", "text-card-foreground"]}>{event.title}</h2>
                  <span class={[
                    "px-2", "py-1", "text-xs", "rounded-full",
                    ...(event.status === "published" 
                      ? ["bg-primary/10", "text-primary"] 
                      : ["bg-muted", "text-muted-foreground"])
                  ]}>
                    {event.status === "published" ? "预约中" : "已结束"}
                  </span>
                </div>
                <div class={["flex", "flex-col", "gap-2", "text-sm", "text-muted-foreground", "mb-4"]}>
                  <span>📍 {event.venue.name}</span>
                  <span>🕒 {new Date(event.startTime).toLocaleString()}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>

        <div class={["flex", "items-center", "justify-center", "gap-4", "mt-10"]}>
          <button
            onclick={handlePrevPage}
            disabled={currentPage === 1}
            class={["text-sm", "text-primary", "disabled:text-muted-foreground", "disabled:cursor-not-allowed"]}
          >
            上一页
          </button>
          <span class={["text-sm", "text-foreground"]}>
            第 {currentPage} / {totalPages} 页
          </span>
          <button
            onclick={handleNextPage}
            disabled={currentPage === totalPages}
            class={["text-sm", "text-primary", "disabled:text-muted-foreground", "disabled:cursor-not-allowed"]}
          >
            下一页
          </button>
        </div>
      {/if}
    </div>

  </div>
</div>