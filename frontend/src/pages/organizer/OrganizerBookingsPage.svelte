<script lang="ts">
  import { ApiError, endpoints, request } from "@/common/api";
  import type {
    EventRecord,
    Page,
    RosterEntry,
    TicketStatus,
  } from "@/common/api/types";
  import Empty from "@/common/components/Empty.svelte";
  import ErrorState from "@/common/components/ErrorState.svelte";
  import Loading from "@/common/components/Loading.svelte";
  import { router } from "@/common/router";
  import { STATUS_LABEL } from "@/common/utils/groupBookings";
  import { formatDateTime } from "@/common/utils/datetime";
  import { TICKET_STATUS_LABEL } from "@/common/utils/labels";

  import { Button } from "$lib/components/ui/button";

  const STATUS_BADGE_CLASS: Record<string, string[]> = {
    reserved: ["bg-primary/10", "text-primary"],
    used: ["bg-secondary", "text-secondary-foreground"],
    cancelled: ["bg-muted", "text-muted-foreground"],
  };

  let loading = $state(true);
  let loadError = $state("");
  let eventTitle = $state("");
  let eventPeriod = $state("");
  let entries = $state<RosterEntry[]>([]);
  let total = $state(0);

  const rawEventId = $derived(router.params.id ?? "");
  const eventId = $derived(
    /^[1-9]\d*$/.test(rawEventId) ? Number(rawEventId) : Number.NaN,
  );

  const verifiedCount = $derived(
    entries.filter((entry) => entry.verifiedAt !== null).length,
  );
  const reservedCount = $derived(
    entries.filter((entry) => entry.status === "reserved").length,
  );

  function describeError(error: unknown): string {
    return error instanceof ApiError
      ? error.message
      : "加载名单失败，请稍后重试";
  }

  async function loadRoster(id: number): Promise<void> {
    loading = true;
    loadError = "";
    try {
      const [event, roster] = await Promise.all([
        request<EventRecord>(endpoints.eventDetail(id)),
        request<Page<RosterEntry>>(
          `${endpoints.eventBookings(id)}?page=1&pageSize=100`,
        ),
      ]);
      eventTitle = event.title;
      eventPeriod = `${formatDateTime(event.startTime)} — ${formatDateTime(event.endTime)}`;
      entries = roster.items;
      total = roster.total;
    } catch (error) {
      loadError = describeError(error);
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    const id = eventId;
    if (Number.isNaN(id)) {
      loading = false;
      loadError = "活动编号不合法，请回到活动列表重新进入";
      return;
    }
    void loadRoster(id);
  });

  function verifyHref(ticketCode: string | null): string {
    if (ticketCode === null || ticketCode.length === 0) {
      return "#/organizer/verify";
    }
    return `#/organizer/verify?code=${encodeURIComponent(ticketCode)}`;
  }

  /** 票面状态是派生字段（enums.md §2.5），不读数据库列。 */
  function ticketStatusOf(entry: RosterEntry): TicketStatus {
    if (entry.status === "cancelled") {
      return "cancelled";
    }
    if (entry.verifiedAt !== null) {
      return "used";
    }
    return "reserved";
  }
</script>

<section class={["flex", "flex-col", "gap-6"]}>
  <header
    class={["flex", "flex-wrap", "items-start", "justify-between", "gap-3"]}
  >
    <div>
      <h1 class={["text-3xl", "font-bold"]}>本场预约名单</h1>
      <p class={["mt-2", "text-muted-foreground"]}>
        {#if eventTitle.length > 0}
          {eventTitle} · {eventPeriod}
        {:else}
          活动编号 #{rawEventId}
        {/if}
      </p>
    </div>
    <div class={["flex", "flex-wrap", "gap-2"]}>
      <Button href="#/organizer/events" variant="outline">返回活动管理</Button>
      <Button href="#/organizer/verify" variant="outline">去核验</Button>
      <Button
        variant="outline"
        disabled={loading || Number.isNaN(eventId)}
        onclick={() => {
          if (!Number.isNaN(eventId)) {
            void loadRoster(eventId);
          }
        }}
      >
        刷新
      </Button>
    </div>
  </header>

  {#if !loading && loadError.length === 0}
    <dl class={["grid", "gap-4", "sm:grid-cols-3"]}>
      <div class={["rounded-xl", "border", "border-border", "bg-card", "p-4"]}>
        <dt class={["text-xs", "text-muted-foreground"]}>预约总数</dt>
        <dd class={["text-2xl", "font-semibold"]}>{total}</dd>
      </div>
      <div class={["rounded-xl", "border", "border-border", "bg-card", "p-4"]}>
        <dt class={["text-xs", "text-muted-foreground"]}>待核验</dt>
        <dd class={["text-2xl", "font-semibold"]}>{reservedCount}</dd>
      </div>
      <div class={["rounded-xl", "border", "border-border", "bg-card", "p-4"]}>
        <dt class={["text-xs", "text-muted-foreground"]}>已核验</dt>
        <dd class={["text-2xl", "font-semibold"]}>{verifiedCount}</dd>
      </div>
    </dl>
  {/if}

  {#if loading}
    <Loading />
  {:else if loadError.length > 0}
    <ErrorState message={loadError} />
  {:else if entries.length === 0}
    <Empty message="本场还没有预约记录" />
  {:else}
    <div class={["overflow-x-auto", "rounded-xl", "border", "border-border"]}>
      <table class={["w-full", "min-w-[760px]", "text-left", "text-sm"]}>
        <thead class={["bg-muted", "text-muted-foreground"]}>
          <tr>
            <th class={["px-4", "py-3", "font-medium"]}>用户</th>
            <th class={["px-4", "py-3", "font-medium"]}>座位</th>
            <th class={["px-4", "py-3", "font-medium"]}>预约状态</th>
            <th class={["px-4", "py-3", "font-medium"]}>票号</th>
            <th class={["px-4", "py-3", "font-medium"]}>核验</th>
            <th class={["px-4", "py-3", "font-medium"]}>操作</th>
          </tr>
        </thead>
        <tbody>
          {#each entries as entry (entry.id)}
            {@const ticketStatus = ticketStatusOf(entry)}
            <tr class={["border-t", "border-border"]}>
              <td class={["px-4", "py-3"]}>
                <div class={["font-medium"]}>{entry.user.name}</div>
                <div class={["text-xs", "text-muted-foreground"]}>
                  {entry.user.email}
                </div>
              </td>
              <td class={["px-4", "py-3"]}>
                {#if entry.seats.length > 0}
                  {entry.seats.map((seat) => seat.label).join("、")}
                {:else}
                  <span class={["text-muted-foreground"]}>—</span>
                {/if}
              </td>
              <td class={["px-4", "py-3"]}>
                <span
                  class={[
                    "rounded-full",
                    "px-2.5",
                    "py-0.5",
                    "text-xs",
                    "font-medium",
                    ...(STATUS_BADGE_CLASS[entry.status] ?? []),
                  ]}
                >
                  {STATUS_LABEL[entry.status]}
                </span>
              </td>
              <td class={["px-4", "py-3"]}>
                {#if entry.ticketCode !== null && entry.ticketCode.length > 0}
                  <code class={["font-mono", "text-xs"]}
                    >{entry.ticketCode}</code
                  >
                  <div class={["text-xs", "text-muted-foreground"]}>
                    {TICKET_STATUS_LABEL[ticketStatus]}
                  </div>
                {:else}
                  <span class={["text-muted-foreground"]}>—</span>
                {/if}
              </td>
              <td class={["px-4", "py-3"]}>
                {#if entry.verifiedAt !== null}
                  <div>{formatDateTime(entry.verifiedAt)}</div>
                  <div class={["text-xs", "text-muted-foreground"]}>
                    核验人 #{entry.verifiedBy ?? "—"}
                  </div>
                {:else}
                  <span class={["text-muted-foreground"]}>未核验</span>
                {/if}
              </td>
              <td class={["px-4", "py-3"]}>
                {#if entry.ticketCode !== null && entry.status === "reserved" && entry.verifiedAt === null}
                  <Button
                    size="sm"
                    variant="outline"
                    href={verifyHref(entry.ticketCode)}
                  >
                    核验签到
                  </Button>
                {:else}
                  <span class={["text-muted-foreground"]}>—</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class={["text-xs", "text-muted-foreground"]}>
      共 {total} 条，当前显示 {entries.length} 条。取消的预约保留在名单中，票面标注“已失效”。
    </p>
  {/if}
</section>
