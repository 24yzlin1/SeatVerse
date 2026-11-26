<script lang="ts">
  import { untrack } from "svelte";
  import { toast } from "svelte-sonner";
  // Aliased: `Error` (component) and `Ticket` (component class name) would
  // otherwise shadow the native Error and the API type inside this file.
  import ErrorComponent from "@/common/Error.svelte";
  import TicketView from "@/pages/tickets/components/TicketView.svelte";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Ticket as TicketRecord } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";
  import { LatestRequest } from "@/common/utils/latestRequest";

  const { params }: { params: Record<string, string> } = $props();

  // The route parameter is the booking id the ticket belongs to.
  const bookingId = $derived(
    /^[1-9]\d*$/.test(params.id ?? "") ? Number(params.id) : Number.NaN,
  );

  let errorMessage = $state("");
  let ticket: TicketRecord | null = $state(null);
  let cancelling = $state(false);
  const loader = new LatestRequest();

  // Cancellation is allowed while the booking is still reserved and the
  // event has not started yet (same rule as the bookings list).
  function isCancellable(currentTicket: TicketRecord | null): boolean {
    return (
      currentTicket !== null &&
      currentTicket.status === "reserved" &&
      Date.now() < Date.parse(currentTicket.event.startTime)
    );
  }
  const cancellable = $derived(isCancellable(ticket));

  async function loadTicket(currentBookingId: number) {
    await loader.run(
      (signal) =>
        request<TicketRecord>(endpoints.bookingTicket(currentBookingId), { signal }),
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

  // Cancel this booking, then refetch the ticket so the badge reflects the
  // latest submission immediately.
  async function cancelTicket() {
    if (ticket === null || cancelling) {
      return;
    }
    cancelling = true;
    try {
      await request(endpoints.bookingCancel(ticket.bookingId), {
        method: "POST",
      });
      window.dispatchEvent(
        new CustomEvent("seatverse:booking-cancelled", {
          detail: {
            bookingId: ticket.bookingId,
            eventId: ticket.event.id,
            seatIds: ticket.seats.map((seat) => seat.id),
          },
        }),
      );
      toast.success("预约已取消，座位已释放");
      await loadTicket(ticket.bookingId);
    } catch (requestError: unknown) {
      toast.error(
        requestError instanceof Error
          ? requestError.message
          : "取消结果未能确认，请刷新预约核对",
      );
      await loadTicket(ticket.bookingId);
    } finally {
      cancelling = false;
    }
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
  <ErrorComponent description={errorMessage} />
{:else if !ticket}
  <!-- Blank while the ticket is loading. -->
{:else}
  <TicketView {ticket} {cancellable} {cancelling} onCancel={cancelTicket} />
{/if}
