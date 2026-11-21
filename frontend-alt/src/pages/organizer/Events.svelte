<script lang="ts">
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { toast } from "svelte-sonner";
  import { RiAddLine, RiLoader4Line } from "remixicon-svelte";

  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Drawer from "$lib/components/ui/drawer";
  import { Input } from "$lib/components/ui/input";
  import * as Item from "$lib/components/ui/item";
  import { Label } from "$lib/components/ui/label";
  import * as Tabs from "$lib/components/ui/tabs";

  import Description from "@/pages/organizer/components/Description.svelte";
  import NavigationLayout from "@/layout/NavigationLayout.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { EventRecord, Page } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { formatDateTime } from "@/common/utils/datetime";
  import {
    deriveEventDisplayStatus,
    EVENT_SHORT_STATUS_LABEL,
    EVENT_STATUS_LABEL,
  } from "@/common/utils/labels";

  // Status literals accepted by PATCH /events/{id}/status.
  type StatusAction = "published" | "closed" | "cancelled";

  let error = $state("");
  let loaded = $state(false);
  let events: EventRecord[] = $state([]);
  let busyEventId = $state<number | null>(null);

  let isCreateDrawerOpen = $state(false);
  let creating = $state(false);
  let createForm = $state({
    title: "",
    description: "",
    startTime: "",
    endTime: "",
  });

  const now = $state(Date.now());

  // Status filter tabs; "all" shows every event owned by the organizer.
  let statusFilter = $state("all");

  const statusFilters = [
    { value: "all", label: "全部" },
    { value: "draft", label: "未发布" },
    { value: "published", label: "预约中" },
    { value: "closed", label: "已停约" },
    { value: "cancelled", label: "已取消" },
  ] as const;

  const visibleEvents = $derived(
    statusFilter === "all"
      ? events
      : events.filter((item) => item.status === statusFilter),
  );

  function describeError(operationError: unknown, fallback: string): string {
    return operationError instanceof ApiError
      ? operationError.message
      : fallback;
  }

  async function loadEvents() {
    try {
      const page = await request<Page<EventRecord>>(
        `${endpoints.events()}?page=1&pageSize=100`,
      );
      // The list endpoint is public and contains other organizers' events;
      // the console only shows events owned by the current organizer.
      const organizerId = authentication.user?.id;
      events = page.items.filter(
        (item) => organizerId !== undefined && item.organizerId === organizerId,
      );
    } catch (requestError: unknown) {
      error = describeError(requestError, "获取活动列表失败");
    } finally {
      loaded = true;
    }
  }

  onMount(loadEvents);

  $effect(() => {
    if (error.length === 0) {
      return;
    }

    toast.error(error);
    error = "";
  });

  async function changeStatus(target: EventRecord, status: StatusAction) {
    busyEventId = target.id;
    try {
      const updated = await request<EventRecord>(
        endpoints.eventStatus(target.id),
        {
          method: "PATCH",
          body: { status },
        },
      );
      events = events.map((item) => (item.id === updated.id ? updated : item));
      toast.success(
        `「${updated.title}」已更新为${EVENT_STATUS_LABEL[updated.status]}`,
      );
    } catch (requestError: unknown) {
      toast.error(describeError(requestError, "操作失败，请稍后重试"));
    } finally {
      busyEventId = null;
    }
  }

  async function submitCreate() {
    const title = createForm.title.trim();
    if (title.length === 0) {
      toast.error("请填写活动标题");
      return;
    }
    if (createForm.startTime.length === 0 || createForm.endTime.length === 0) {
      toast.error("请填写开始与结束时间");
      return;
    }

    const start = new Date(createForm.startTime);
    const end = new Date(createForm.endTime);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      toast.error("时间格式不正确，请重新选择");
      return;
    }
    if (end.getTime() <= start.getTime()) {
      toast.error("结束时间必须晚于开始时间");
      return;
    }

    creating = true;
    try {
      const created = await request<EventRecord>(endpoints.eventCreate(), {
        method: "POST",
        body: {
          title,
          description: createForm.description.trim(),
          startTime: start.toISOString(),
          endTime: end.toISOString(),
        },
      });
      events = [created, ...events];
      isCreateDrawerOpen = false;
      createForm = { title: "", description: "", startTime: "", endTime: "" };
      toast.success("活动已创建");
    } catch (requestError: unknown) {
      toast.error(describeError(requestError, "创建失败，请稍后重试"));
    } finally {
      creating = false;
    }
  }
</script>

<NavigationLayout {panel} {body} />

{#snippet panel()}
  <Description category="events" />
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
    <Button
      size="icon"
      variant="secondary"
      onclick={() => (isCreateDrawerOpen = true)}
    >
      <RiAddLine />
    </Button>
  </div>
  <div class={["px-2", "flex", "flex-col"]}>
    {#if !loaded}
      <!-- TODO: show a skeleton placeholder while the organizer events are loading. -->
    {:else}
      {#each visibleEvents as event (event.id)}
        {@const displayStatus = deriveEventDisplayStatus(event, now)}
        <Item.Root>
          <Item.Media class={["size-8"]}>
            <Avatar.Root class={["rounded-lg"]}>
              <Avatar.Fallback>
                {event.title.charAt(0)}
              </Avatar.Fallback>
            </Avatar.Root>
          </Item.Media>
          <Item.Content class={["overflow-hidden"]}>
            <Item.Title class={["line-clamp-1"]}>
              {event.title}
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
                {formatDateTime(event.startTime)} —
                {formatDateTime(event.endTime)}
              </Item.Description>
            </div>
            <div class={["flex", "flex-wrap", "gap-2"]}>
              {#if event.status === "draft"}
                <Button
                  size="sm"
                  disabled={busyEventId === event.id}
                  onclick={() => {
                    void changeStatus(event, "published");
                  }}
                >
                  发布
                </Button>
              {/if}
              {#if event.status === "published"}
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={busyEventId === event.id}
                  onclick={() => {
                    void changeStatus(event, "closed");
                  }}
                >
                  停止预约
                </Button>
              {/if}
              {#if event.status === "draft" || event.status === "published"}
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={busyEventId === event.id}
                  onclick={() => {
                    void changeStatus(event, "cancelled");
                  }}
                >
                  取消活动
                </Button>
              {/if}
              <Button
                size="sm"
                variant="secondary"
                onclick={() => push(`/organizer/events/${event.id}/bookings`)}
              >
                查看名单
              </Button>
            </div>
          </Item.Content>
        </Item.Root>
      {/each}
    {/if}
  </div>
{/snippet}

<Drawer.Root bind:open={isCreateDrawerOpen}>
  <Drawer.Content class={["px-8", "h-[85vh]"]}>
    <Drawer.Title class={["px-4", "py-8"]}>新建活动</Drawer.Title>
    <div class={["h-full", "px-4"]}>
      <div class={["flex", "flex-col", "gap-3", "w-full"]}>
        <div class={["flex", "flex-col", "gap-3"]}>
          <Label for="organizer-event-title">活动标题</Label>
          <Input
            id="organizer-event-title"
            bind:value={createForm.title}
            maxlength={120}
            disabled={creating}
          />
        </div>
        <div class={["flex", "flex-col", "gap-3"]}>
          <Label for="organizer-event-description">活动简介</Label>
          <textarea
            id="organizer-event-description"
            class={[
              "min-h-20",
              "rounded-3xl",
              "border",
              "border-transparent",
              "bg-input/50",
              "px-3",
              "py-2",
              "text-sm",
              "outline-none",
              "transition-[color,box-shadow,background-color]",
              "focus-visible:border-ring",
              "focus-visible:ring-3",
              "focus-visible:ring-ring/30",
              "disabled:pointer-events-none",
              "disabled:opacity-50",
            ]}
            bind:value={createForm.description}
            disabled={creating}></textarea>
        </div>
        <div class={["flex", "flex-col", "gap-3"]}>
          <Label for="organizer-event-start-time">开始时间</Label>
          <Input
            id="organizer-event-start-time"
            type="datetime-local"
            bind:value={createForm.startTime}
            disabled={creating}
          />
        </div>
        <div class={["flex", "flex-col", "gap-3"]}>
          <Label for="organizer-event-end-time">结束时间</Label>
          <Input
            id="organizer-event-end-time"
            type="datetime-local"
            bind:value={createForm.endTime}
            disabled={creating}
          />
        </div>
      </div>
    </div>
    <Drawer.Footer class={["px-4", "py-8"]}>
      <Button
        disabled={creating}
        onclick={() => {
          void submitCreate();
        }}
      >
        {#if creating}
          <RiLoader4Line class={["animate-spin"]} />
        {/if}
        创建
      </Button>
    </Drawer.Footer>
  </Drawer.Content>
</Drawer.Root>
