<script lang="ts">
  import type { Booking, BookingStatus } from "@/common/api";
  import { STATUS_LABEL } from "@/common/utils/groupBookings";

  const {
    booking,
    onCancel,
    cancelling,
    actionDisabled,
  }: {
    booking: Booking;
    onCancel: (id: number) => void;
    cancelling: boolean;
    actionDisabled: boolean;
  } = $props();
  let confirming = $state(false);
  const canCancel = $derived(
    booking.status === "reserved" &&
      Date.parse(booking.event.startTime) > Date.now(),
  );

  const STATUS_CLASS: Record<BookingStatus, string> = {
    reserved: "bg-primary/10 text-primary",
    cancelled: "bg-muted text-muted-foreground",
    used: "bg-secondary text-secondary-foreground",
  };

  const statusClass = $derived(STATUS_CLASS[booking.status]);
  const statusLabel = $derived(STATUS_LABEL[booking.status]);
  const seats = $derived(booking.seats.map((seat) => seat.label).join("、"));
  const period = $derived(
    `${formatDate(booking.event.startTime)} — ${formatDate(booking.event.endTime)}`,
  );

  function formatDate(value: string): string {
    return new Date(value).toLocaleString("zh-CN");
  }
</script>

<article
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
  <header class={["flex", "items-start", "justify-between", "gap-4"]}>
    <h2
      class={[
        "break-words",
        "text-lg",
        "font-semibold",
        "text-card-foreground",
      ]}
    >
      {booking.event.title}
    </h2>
    <span
      class={[
        "shrink-0",
        "rounded-full",
        "px-3",
        "py-1",
        "text-xs",
        "font-medium",
        statusClass,
      ]}
    >
      {statusLabel}
    </span>
  </header>

  <dl
    class={["grid", "grid-cols-1", "gap-2", "text-sm", "text-muted-foreground"]}
  >
    <div class={["flex", "gap-2"]}>
      <dt class={["shrink-0", "font-medium", "text-foreground"]}>场馆</dt>
      <dd>{booking.event.venue.name}</dd>
    </div>
    <div class={["flex", "gap-2"]}>
      <dt class={["shrink-0", "font-medium", "text-foreground"]}>时间</dt>
      <dd>{period}</dd>
    </div>
    <div class={["flex", "gap-2"]}>
      <dt class={["shrink-0", "font-medium", "text-foreground"]}>座位</dt>
      <dd>{seats}</dd>
    </div>
    <div class={["flex", "gap-2"]}>
      <dt class={["shrink-0", "font-medium", "text-foreground"]}>预约时间</dt>
      <dd>{formatDate(booking.createdAt)}</dd>
    </div>
  </dl>
  <p class="text-xs text-muted-foreground break-all">
    预约编号：{booking.id} · 票号：{booking.ticketCode}
  </p>
  <div class="flex flex-wrap items-center gap-3 text-sm">
    <a
      class="underline underline-offset-4"
      href={`#/events/${booking.event.id}/seats`}>查看本场座位</a
    >
    {#if canCancel}
      {#if confirming}
        <span>确认取消并释放座位？</span>
        <button
          type="button"
          class="rounded-md border px-3 py-2"
          disabled={actionDisabled}
          onclick={() => {
            confirming = false;
            onCancel(booking.id);
          }}>确认取消</button
        >
        <button
          type="button"
          class="rounded-md border px-3 py-2"
          disabled={actionDisabled}
          onclick={() => (confirming = false)}>返回</button
        >
      {:else}
        <button
          type="button"
          class="rounded-md border px-3 py-2"
          disabled={actionDisabled}
          onclick={() => (confirming = true)}
          >{cancelling ? "正在取消…" : "取消预约"}</button
        >
      {/if}
    {/if}
  </div>
</article>
