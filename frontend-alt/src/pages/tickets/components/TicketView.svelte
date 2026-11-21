<script lang="ts">
  import JsBarcode from "jsbarcode";
  import { renderSVG } from "uqr";
  import { toast } from "svelte-sonner";
  import {
    RiCalendarLine,
    RiCheckboxCircleLine,
    RiFileCopyLine,
    RiGroupLine,
    RiMapPinLine,
    RiQrCodeLine,
  } from "remixicon-svelte";

  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import Button from "$lib/components/ui/button/button.svelte";
  import * as Item from "$lib/components/ui/item";

  import type { Ticket } from "@/common/api";
  import { formatDateTime } from "@/common/utils/datetime";
  import { BOOKING_STATUS_LABEL } from "@/common/utils/groupBookings";

  const { ticket }: { ticket: Ticket } = $props();

  // Pure view state; the barcode is redrawn whenever the ticket changes.
  let barcodeElement = $state<SVGSVGElement | null>(null);

  $effect(() => {
    if (barcodeElement === null) return;
    // The ticket code is Crockford Base32 (uppercase alphanumerics), which
    // Code 39 covers without extensions.
    JsBarcode(barcodeElement, ticket.ticketCode, {
      format: "CODE39",
      displayValue: false,
      margin: 0,
      height: 48,
      width: 2,
    });
  });

  async function copyTicketCode() {
    try {
      await navigator.clipboard.writeText(ticket.ticketCode);
      toast.success("票号已复制");
    } catch {
      toast.error("复制失败，请手动选中票号复制");
    }
  }
</script>

<div class={["pt-4", "px-6"]}>
  <Item.Root variant="muted" class={["flex-nowrap", "overflow-hidden"]}>
    <Item.Media variant="image">
      <Avatar.Root size="lg">
        <Avatar.Fallback>
          {ticket.event.title.charAt(0)}
        </Avatar.Fallback>
      </Avatar.Root>
    </Item.Media>
    <Item.Content>
      <Item.Title>{ticket.event.title}</Item.Title>
      <div class={["flex", "gap-2"]}>
        <Badge
          variant={ticket.status === "cancelled" ? "destructive" : "default"}
        >
          {BOOKING_STATUS_LABEL[ticket.status]}
        </Badge>
      </div>
    </Item.Content>
  </Item.Root>
  <div class={["py-4", "flex", "flex-col", "gap-2"]}>
    <Item.Root class={["p-0"]}>
      <Item.Media class={["size-8"]} variant="icon">
        <RiGroupLine />
      </Item.Media>
      <Item.Content>
        <Item.Title>
          {ticket.seats.map((seat) => seat.label).join("、")}
        </Item.Title>
      </Item.Content>
    </Item.Root>
    <Item.Root class={["p-0"]}>
      <Item.Media class={["size-8"]} variant="icon">
        <RiCalendarLine />
      </Item.Media>
      <Item.Content>
        <Item.Title>
          {formatDateTime(ticket.issuedAt)}
        </Item.Title>
      </Item.Content>
    </Item.Root>
    <Item.Root class={["p-0"]}>
      <Item.Media class={["size-8"]} variant="icon">
        <RiCheckboxCircleLine />
      </Item.Media>
      <Item.Content>
        <Item.Title>
          {ticket.verifiedAt === null ? "—" : formatDateTime(ticket.verifiedAt)}
        </Item.Title>
      </Item.Content>
    </Item.Root>
    <Item.Root class={["p-0"]}>
      <Item.Media class={["size-8"]} variant="icon">
        <RiMapPinLine />
      </Item.Media>
      <Item.Content>
        <Item.Title>
          {ticket.event.venue.name}
        </Item.Title>
      </Item.Content>
    </Item.Root>
  </div>
</div>
<div class={["px-6", "py-4"]}>
  <Item.Root variant="muted">
    <div
      class={[
        "w-full",
        "py-4",
        "flex",
        "flex-col",
        "gap-4",
        "items-center",
        "overflow-hidden",
      ]}
    >
      <Item.Root class={["p-0"]}>
        <Item.Media class={["size-8"]} variant="icon">
          <RiQrCodeLine />
        </Item.Media>
        <Item.Content>
          <Item.Title>入场码</Item.Title>
        </Item.Content>
      </Item.Root>
      <div class={["size-48", "p-2", "[&>svg]:size-full"]}>
        {@html renderSVG(ticket.ticketCode)}
      </div>
      <div
        class={["w-full", "py-2", "flex", "justify-center", "overflow-hidden"]}
      >
        <svg bind:this={barcodeElement}></svg>
      </div>
      <div class={["flex", "items-center", "gap-2", "max-w-full"]}>
        <p
          class={[
            "font-mono",
            "text-lg",
            "tracking-widest",
            "break-all",
            "text-center",
          ]}
        >
          {ticket.ticketCode}
        </p>
        <Button
          variant="ghost"
          size="icon"
          aria-label="复制票号"
          title="复制票号"
          onclick={() => {
            void copyTicketCode();
          }}
        >
          <RiFileCopyLine />
        </Button>
      </div>
    </div>
  </Item.Root>
</div>
