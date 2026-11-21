<script lang="ts">
  import { untrack } from "svelte";
  import Error from "@/common/Error.svelte";
  import TicketView from "@/pages/tickets/components/TicketView.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Ticket } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { LatestRequest } from "@/common/utils/latestRequest";

  const { params }: { params: Record<string, string> } = $props();

  // The route parameter is the booking id the ticket belongs to.
  const bookingId = $derived(
    /^[1-9]\d*$/.test(params.id ?? "") ? Number(params.id) : Number.NaN,
  );

  let errorMessage = $state("");
  let ticket: Ticket | null = $state(null);
  const loader = new LatestRequest();

  async function loadTicket(currentBookingId: number) {
    await loader.run(
      (signal) =>
        request<Ticket>(endpoints.bookingTicket(currentBookingId), { signal }),
      (value) => {
        ticket = value;
      },
      (requestError) => {
        errorMessage =
          requestError instanceof ApiError
            ? requestError.message
            : "获取电子票失败";
      },
    );
  }

  // Reload the ticket whenever the route booking id changes.
  $effect(() => {
    const currentId = bookingId;
    const identity = authentication.token;
    ticket = null;
    errorMessage = "";
    if (!Number.isSafeInteger(currentId)) {
      errorMessage = "无效的预约 ID";
      return;
    }
    untrack(() => {
      void loadTicket(currentId);
    });
    void identity;
    return () => loader.cancel();
  });
</script>

{#if errorMessage.length !== 0}
  <Error description={errorMessage} />
{:else if !ticket}
  <!-- TODO: show a skeleton placeholder while the ticket is loading. -->
{:else}
  <TicketView {ticket} />
{/if}
