<script lang="ts">
  import type { Booking, BookingStatus } from "@/common/api";

  const { booking }: { booking: Booking } = $props();

  interface StatusStyle {
    label: string;
    className: string;
  }

  const STATUS: Record<BookingStatus, StatusStyle> = {
    reserved: { label: "待参加", className: "bg-primary/10 text-primary" },
    cancelled: { label: "已取消", className: "bg-muted text-muted-foreground" },
    used: { label: "已签到", className: "bg-secondary text-secondary-foreground" },
  };

  const status = $derived(STATUS[booking.status]);
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
    <h2 class={["break-words", "text-lg", "font-semibold", "text-card-foreground"]}>
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
        status.className,
      ]}
    >
      {status.label}
    </span>
  </header>

  <dl class={["grid", "grid-cols-1", "gap-2", "text-sm", "text-muted-foreground"]}>
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
</article>
