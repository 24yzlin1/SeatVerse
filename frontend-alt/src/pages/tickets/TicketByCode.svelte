<script lang="ts">
  import { untrack } from "svelte";
  import Error from "@/common/Error.svelte";
  import TicketView from "@/pages/tickets/components/TicketView.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Ticket } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { LatestRequest } from "@/common/utils/latestRequest";

  const { params }: { params: Record<string, string> } = $props();

  // Input normalization (ticket-qr.md §2.3): trim, drop hyphens, uppercase.
  function normalizeTicketCode(value: string): string {
    return value.trim().replace(/-/g, "").toUpperCase();
  }

  const ticketCode = $derived(normalizeTicketCode(params.code ?? ""));

  let errorMessage = $state("");
  let ticket: Ticket | null = $state(null);
  const loader = new LatestRequest();

  async function loadTicket(currentCode: string) {
    await loader.run(
      (signal) =>
        request<Ticket>(endpoints.ticketByCode(currentCode), { signal }),
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

  // Reload the ticket whenever the route ticket code changes.
  $effect(() => {
    const currentCode = ticketCode;
    const identity = authentication.token;
    ticket = null;
    errorMessage = "";
    if (currentCode.length === 0) {
      errorMessage = "缺少票号";
      return;
    }
    untrack(() => {
      void loadTicket(currentCode);
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
