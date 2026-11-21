<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import type { Booking } from "@/common/api";

  const {
    booking,
    onShowDetails,
  }: { booking: Booking; onShowDetails?: () => void } = $props();
</script>

<section
  class="rounded-lg border p-4 flex flex-col gap-2"
  role="status"
  aria-label="预约成功"
>
  <p>预约成功 · 预约编号 {booking.id}</p>
  <p>座位：{booking.seats.map((seat) => seat.label).join("、")}</p>
  <p class="break-all">票号：{booking.ticketCode}</p>
  <nav class="flex flex-wrap gap-2" aria-label="预约结果导航">
    <Button href={`#/bookings/${booking.id}/ticket`}>查看电子票</Button>
    <Button variant="secondary" href="#/bookings">我的预约</Button>
    {#if onShowDetails}
      <Button variant="secondary" onclick={onShowDetails}>查看本场活动</Button>
    {:else}
      <Button variant="secondary" href={`#/events/${booking.event.id}`}
        >查看本场活动</Button
      >
    {/if}
  </nav>
</section>
