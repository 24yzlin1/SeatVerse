<script lang="ts">
  import Error from "@/common/Error.svelte";
  import TicketView from "@/pages/tickets/components/TicketView.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Ticket } from "@/common/api";

  const { params }: { params: Record<string, string> } = $props();

  // The route parameter is the booking id the ticket belongs to.
  const bookingId = $derived(
    /^[1-9]\d*$/.test(params.id ?? "") ? Number(params.id) : Number.NaN,
  );

  let errorMessage = $state("");
  let ticket: Ticket | null = $state(null);

  async function loadTicket(currentBookingId: number) {
    try {
      ticket = await request<Ticket>(endpoints.bookingTicket(currentBookingId));
    } catch (requestError: unknown) {
      errorMessage =
        requestError instanceof ApiError
          ? requestError.message
          : "获取电子票失败";
    }
  }

  // Reload the ticket whenever the route booking id changes.
  $effect(() => {
    const currentId = bookingId;
    ticket = null;
    errorMessage = "";
    if (!Number.isSafeInteger(currentId)) {
      errorMessage = "无效的预约 ID";
      return;
    }
    void loadTicket(currentId);
  });
</script>

{#if errorMessage.length !== 0}
  <Error description={errorMessage} />
{:else if !ticket}
  <!-- TODO: show a skeleton placeholder while the ticket is loading. -->
{:else}
  <TicketView {ticket} />
{/if}
