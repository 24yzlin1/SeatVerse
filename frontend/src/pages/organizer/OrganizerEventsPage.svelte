<script lang="ts">
  import { onMount } from "svelte";

  import { ApiError, endpoints, request } from "@/common/api";
  import type { EventRecord, Page } from "@/common/api/types";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import Loading from "@/common/components/Loading.svelte";
  import { auth } from "@/common/stores/auth.svelte";
  import { formatDateTime } from "@/common/utils/datetime";
  import {
    EVENT_DISPLAY_STATUS_LABEL,
    EVENT_STATUS_LABEL,
    deriveEventDisplayStatus,
  } from "@/common/utils/labels";
  import type { EventDisplayStatus } from "@/common/utils/labels";

  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";

  type StatusAction = "published" | "closed" | "cancelled";

  /** 状态徽标样式：只用主题令牌，不硬编码色值（03 号规范 §9.1）。 */
  const STATUS_BADGE_CLASS: Record<EventDisplayStatus, string[]> = {
    draft: ["bg-muted", "text-muted-foreground"],
    published: ["bg-secondary", "text-secondary-foreground"],
    ongoing: ["bg-primary", "text-primary-foreground"],
    ended: ["bg-muted", "text-muted-foreground"],
    stopped: ["bg-secondary", "text-secondary-foreground"],
    cancelled: ["bg-destructive/10", "text-destructive"],
  };

  let events = $state<EventRecord[]>([]);
  let loading = $state(true);
  let loadError = $state("");
  let notice = $state("");
  let busyEventId = $state<number | null>(null);

  let formOpen = $state(false);
  let creating = $state(false);
  let formError = $state("");
  let form = $state({
    title: "",
    description: "",
    startTime: "",
    endTime: "",
  });

  const organizerName = $derived(auth.user?.name ?? "");

  function describeError(error: unknown): string {
    return error instanceof ApiError ? error.message : "操作失败，请稍后重试";
  }

  async function loadEvents(): Promise<void> {
    loading = true;
    loadError = "";
    try {
      const page = await request<Page<EventRecord>>(
        `${endpoints.events()}?page=1&pageSize=100`,
      );
      const organizerId = auth.user?.id ?? null;
      // 活动列表是公开接口，含他人活动；后台只展示自己的。
      events = page.items.filter(
        (item) => organizerId !== null && item.organizerId === organizerId,
      );
    } catch (error) {
      loadError = describeError(error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    void loadEvents();
  });

  async function changeStatus(
    event: EventRecord,
    status: StatusAction,
  ): Promise<void> {
    busyEventId = event.id;
    notice = "";
    try {
      const updated = await request<EventRecord>(
        endpoints.eventStatus(event.id),
        {
          method: "PATCH",
          body: { status },
        },
      );
      events = events.map((item) => (item.id === updated.id ? updated : item));
      notice = `「${updated.title}」已更新为${EVENT_STATUS_LABEL[updated.status]}`;
    } catch (error) {
      notice = describeError(error);
    } finally {
      busyEventId = null;
    }
  }

  function openForm(): void {
    formOpen = true;
    formError = "";
    notice = "";
  }

  function closeForm(): void {
    formOpen = false;
    formError = "";
  }

  async function submitForm(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    formError = "";

    const title = form.title.trim();
    if (title.length === 0) {
      formError = "请填写活动标题";
      return;
    }
    if (form.startTime.length === 0 || form.endTime.length === 0) {
      formError = "请填写开始与结束时间";
      return;
    }

    const start = new Date(form.startTime);
    const end = new Date(form.endTime);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      formError = "时间格式不正确，请重新选择";
      return;
    }
    if (end.getTime() <= start.getTime()) {
      formError = "结束时间必须晚于开始时间";
      return;
    }

    creating = true;
    try {
      const created = await request<EventRecord>(endpoints.eventCreate(), {
        method: "POST",
        body: {
          title,
          description: form.description.trim(),
          startTime: start.toISOString(),
          endTime: end.toISOString(),
        },
      });
      events = [created, ...events];
      formOpen = false;
      form = { title: "", description: "", startTime: "", endTime: "" };
      notice = "活动已创建为草稿，确认信息无误后点击「发布」";
    } catch (error) {
      formError = describeError(error);
    } finally {
      creating = false;
    }
  }
</script>

<section class={["flex", "flex-col", "gap-6"]}>
  <header
    class={["flex", "flex-wrap", "items-start", "justify-between", "gap-3"]}
  >
    <div>
      <h1 class={["text-3xl", "font-bold"]}>主办方后台</h1>
      <p class={["mt-2", "text-muted-foreground"]}>
        {#if organizerName.length > 0}
          当前身份：{organizerName} · 只能管理自己创建的活动
        {:else}
          管理自己创建的活动、名单与现场核验
        {/if}
      </p>
    </div>
    <div class={["flex", "flex-wrap", "gap-2"]}>
      <Button href="#/organizer/verify" variant="outline">扫码核验</Button>
      <Button onclick={openForm} disabled={creating}>新建活动</Button>
    </div>
  </header>

  {#if notice.length > 0}
    <p
      role="status"
      class={[
        "rounded-xl",
        "bg-accent",
        "px-4",
        "py-2",
        "text-sm",
        "text-accent-foreground",
      ]}
    >
      {notice}
    </p>
  {/if}

  {#if formOpen}
    <form
      class={[
        "flex",
        "flex-col",
        "gap-4",
        "rounded-xl",
        "border",
        "border-border",
        "bg-card",
        "p-6",
      ]}
      onsubmit={submitForm}
    >
      <h2 class={["text-xl", "font-semibold"]}>新建活动</h2>

      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="title">活动标题</Label>
        <Input
          id="title"
          bind:value={form.title}
          maxlength={120}
          placeholder="例如：周五晚间讲座"
          disabled={creating}
        />
      </div>

      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="description">活动简介</Label>
        <textarea
          id="description"
          class={[
            "min-h-20",
            "rounded-xl",
            "border",
            "border-input",
            "bg-input/50",
            "px-3",
            "py-2",
            "text-sm",
            "outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-ring",
          ]}
          bind:value={form.description}
          placeholder="一句话说明活动内容（可留空）"
          disabled={creating}></textarea>
      </div>

      <div class={["grid", "gap-4", "sm:grid-cols-2"]}>
        <div class={["flex", "flex-col", "gap-2"]}>
          <Label for="startTime">开始时间</Label>
          <Input
            id="startTime"
            type="datetime-local"
            bind:value={form.startTime}
            disabled={creating}
          />
        </div>
        <div class={["flex", "flex-col", "gap-2"]}>
          <Label for="endTime">结束时间</Label>
          <Input
            id="endTime"
            type="datetime-local"
            bind:value={form.endTime}
            disabled={creating}
          />
        </div>
      </div>

      <p class={["text-xs", "text-muted-foreground"]}>
        第一版只有一个预设场馆，创建时由服务端自动绑定，前端不提供场馆选择。
      </p>

      {#if formError.length > 0}
        <p class={["text-sm", "font-medium", "text-destructive"]} role="alert">
          {formError}
        </p>
      {/if}

      <div class={["flex", "flex-wrap", "gap-2"]}>
        <Button type="submit" disabled={creating}>
          {creating ? "创建中…" : "创建草稿"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onclick={closeForm}
          disabled={creating}
        >
          取消
        </Button>
      </div>
    </form>
  {/if}

  {#if loading}
    <Loading />
  {:else if loadError.length > 0}
    <ErrorState message={loadError} />
  {:else if events.length === 0}
    <Empty message="还没有你创建的活动，点击「新建活动」开始" />
  {:else}
    <ul class={["grid", "gap-4"]}>
      {#each events as event (event.id)}
        {@const displayStatus = deriveEventDisplayStatus(event)}
        <li
          class={[
            "flex",
            "flex-col",
            "gap-4",
            "rounded-xl",
            "border",
            "border-border",
            "bg-card",
            "p-6",
          ]}
        >
          <div
            class={[
              "flex",
              "flex-wrap",
              "items-start",
              "justify-between",
              "gap-3",
            ]}
          >
            <div>
              <h2 class={["text-xl", "font-semibold"]}>{event.title}</h2>
              <p class={["mt-1", "text-sm", "text-muted-foreground"]}>
                {formatDateTime(event.startTime)} — {formatDateTime(
                  event.endTime,
                )}
              </p>
              <p class={["text-sm", "text-muted-foreground"]}>
                场馆：{event.venue.name} · 活动编号 #{event.id}
              </p>
            </div>
            <span
              class={[
                "shrink-0",
                "rounded-full",
                "px-3",
                "py-1",
                "text-xs",
                "font-medium",
                ...STATUS_BADGE_CLASS[displayStatus],
              ]}
            >
              {EVENT_DISPLAY_STATUS_LABEL[displayStatus]}
            </span>
          </div>

          {#if event.description.length > 0}
            <p class={["text-sm"]}>{event.description}</p>
          {/if}

          <div class={["flex", "flex-wrap", "gap-2"]}>
            {#if event.status === "draft"}
              <Button
                size="sm"
                onclick={() => {
                  void changeStatus(event, "published");
                }}
                disabled={busyEventId === event.id}
              >
                发布
              </Button>
            {/if}
            {#if event.status === "published"}
              <Button
                size="sm"
                variant="outline"
                onclick={() => {
                  void changeStatus(event, "closed");
                }}
                disabled={busyEventId === event.id}
              >
                停止预约
              </Button>
            {/if}
            {#if event.status === "draft" || event.status === "published"}
              <Button
                size="sm"
                variant="outline"
                onclick={() => {
                  void changeStatus(event, "cancelled");
                }}
                disabled={busyEventId === event.id}
              >
                取消活动
              </Button>
            {/if}
            <Button
              size="sm"
              variant="outline"
              href={`#/organizer/events/${event.id}/bookings`}
            >
              查看名单
            </Button>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</section>
