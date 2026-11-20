<script lang="ts">
  import { request, ApiError } from "@/common/api";
  import type { EventSummary } from "@/common/api/types";
  import Loading from "@/common/components/Loading.svelte";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import { router } from "@/common/router";
  import { onMount, untrack } from "svelte";
  import {
    bookingBlockReason,
    eventStatusLabel,
  } from "@/common/utils/eventAvailability";

  import { Button } from "$lib/components/ui/button";
  import { RiMapPinLine, RiTimeLine } from "remixicon-svelte";

  const id = $derived(router.params.id ?? "");

  let pageState = $state<"loading" | "error" | "empty" | "success">("loading");
  let event = $state<EventSummary | null>(null);
  let errorMessage = $state("");
  let loadVersion = 0;
  let loadController: AbortController | null = null;
  let now = $state(Date.now());
  const blockReason = $derived(
    event ? bookingBlockReason(event, now) : "正在加载活动",
  );
  onMount(() => {
    const timer = window.setInterval(() => {
      now = Date.now();
    }, 1000);
    return () => clearInterval(timer);
  });

  async function fetchEventDetail(currentId: string) {
    const version = ++loadVersion;
    loadController?.abort();
    const controller = new AbortController();
    loadController = controller;
    pageState = "loading";
    event = null;
    errorMessage = "";

    if (
      !/^[1-9]\d*$/.test(currentId) ||
      !Number.isSafeInteger(Number(currentId))
    ) {
      errorMessage = "无效的活动 ID";
      pageState = "error";
      return;
    }

    try {
      const res = await request<EventSummary>(
        `/events/${encodeURIComponent(currentId)}`,
        {
          method: "GET",
          signal: controller.signal,
        },
      );
      if (version !== loadVersion || controller.signal.aborted) return;

      if (!res) {
        pageState = "empty";
        return;
      }
      if (res.id !== Number(currentId)) {
        throw new Error("活动编号与当前页面不一致");
      }

      event = res;
      pageState = "success";
    } catch (error: unknown) {
      if (version !== loadVersion || controller.signal.aborted) return;
      if (error instanceof ApiError) {
        errorMessage = error.message;
      } else {
        errorMessage = "获取活动详情失败";
      }
      pageState = "error";
    }
  }

  function goToSeatMap() {
    if (event && !blockReason && pageState === "success") {
      router.navigate(`/events/${event.id}/seats`);
    }
  }

  $effect(() => {
    const currentId = id;
    untrack(() => void fetchEventDetail(currentId));
    return () => {
      loadVersion++;
      loadController?.abort();
    };
  });
</script>

<div class={["min-h-screen", "bg-background", "p-8"]}>
  <div class={["max-w-3xl", "mx-auto"]}>
    <Button
      variant="ghost"
      onclick={() => router.navigate("/events")}
      class={["mb-8"]}
    >
      ← 返回活动列表
    </Button>

    {#if pageState === "loading"}
      <Loading />
    {:else if pageState === "error"}
      <ErrorState message={errorMessage} />
    {:else if pageState === "empty"}
      <Empty message="活动不存在或已下架" />
    {:else if pageState === "success" && event}
      <div
        class={[
          "bg-card",
          "border",
          "border-border",
          "rounded-2xl",
          "p-8",
          "shadow-sm",
        ]}
      >
        <div class={["flex", "justify-between", "items-start", "mb-6"]}>
          <h1 class={["text-3xl", "font-bold", "text-foreground"]}>
            {event.title}
          </h1>
          <span
            class={[
              "px-3",
              "py-1",
              "text-sm",
              "font-medium",
              "rounded-full",
              ...(event.status === "published"
                ? ["bg-primary/10", "text-primary"]
                : ["bg-muted", "text-muted-foreground"]),
            ]}
          >
            {eventStatusLabel(event, now)}
          </span>
        </div>

        <div
          class={[
            "flex",
            "flex-col",
            "gap-4",
            "text-base",
            "text-muted-foreground",
            "mb-10",
          ]}
        >
          <div class={["flex", "items-center", "gap-3"]}>
            <span class={["font-medium", "text-foreground", "w-20"]}
              >活动场馆</span
            >
            <RiMapPinLine class={["size-4"]} />
            <span> {event.venue.name}</span>
          </div>
          <div class={["flex", "items-center", "gap-3"]}>
            <span class={["font-medium", "text-foreground", "w-20"]}
              >开始时间</span
            >
            <RiTimeLine class={["size-4"]} />
            <span> {new Date(event.startTime).toLocaleString()}</span>
          </div>
          <div class={["flex", "items-center", "gap-3"]}>
            <span class={["font-medium", "text-foreground", "w-20"]}
              >结束时间</span
            >
            <RiTimeLine class={["size-4"]} />
            <span> {new Date(event.endTime).toLocaleString()}</span>
          </div>
        </div>

        <div
          class={["flex", "justify-end", "border-t", "border-border", "pt-6"]}
        >
          <Button
            onclick={goToSeatMap}
            disabled={Boolean(blockReason)}
            class={["px-8", "h-11"]}
          >
            {blockReason || "进入选座（3D / 平面）"}
          </Button>
        </div>
      </div>
    {/if}
  </div>
</div>
