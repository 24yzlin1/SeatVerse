<script lang="ts">
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { RiCheckLine, RiCameraLine, RiQrScan2Line } from "remixicon-svelte";

  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import * as Item from "$lib/components/ui/item";
  import * as Tabs from "$lib/components/ui/tabs";

  import Description from "@/pages/organizer/components/Description.svelte";
  import NavigationLayout from "@/layout/NavigationLayout.svelte";
  import TicketView from "@/pages/tickets/components/TicketView.svelte";
  import { getBarcodeDetectorConstructor } from "@/common/utils/barcode";
  import type { BarcodeDetectorInstance } from "@/common/utils/barcode";
  import { ApiError, endpoints, request } from "@/common/api";
  import type { Page, Ticket } from "@/common/api";
  import { formatDateTime } from "@/common/utils/datetime";

  // Canonical ticket code: 20-character Crockford Base32 (ticket-qr.md §2.1).
  const TICKET_CODE_PATTERN = /^[0-9A-HJKMNP-TV-Z]{20}$/;

  type CameraState = "idle" | "starting" | "running" | "unsupported";

  let verifyTab = $state("verify");

  let ticketCodeInput = $state("");
  let verifying = $state(false);
  let verifiedTicket: Ticket | null = $state(null);

  // Server-backed verification history (GET /tickets/verify/history);
  // survives page refreshes instead of living in session memory.
  let historyItems = $state<Ticket[]>([]);
  let historyPage = $state(0);
  let historyTotal = $state(0);
  let historyLoading = $state(false);
  let historyError = $state("");

  let cameraState = $state<CameraState>("idle");
  let videoElement = $state<HTMLVideoElement | null>(null);
  let stream: MediaStream | null = null;
  let scanning = false;

  const isCameraActive = $derived(
    cameraState === "running" || cameraState === "starting",
  );

  // Input normalization (ticket-qr.md §2.3): trim, drop hyphens, uppercase.
  function normalizeTicketCode(value: string): string {
    return value.trim().replace(/-/g, "").toUpperCase();
  }

  onMount(() => {
    // Load persisted verification history as soon as the page opens.
    void loadHistory(true);
    // Release the camera when the page unmounts.
    return () => stopCamera();
  });

  // Load (or append) a page of the organizer's verification history.
  async function loadHistory(reset: boolean) {
    if (historyLoading) {
      return;
    }
    const targetPage = reset ? 1 : historyPage + 1;
    historyLoading = true;
    historyError = "";
    try {
      const page = await request<Page<Ticket>>(
        `${endpoints.ticketVerifyHistory()}?page=${targetPage}&pageSize=20`,
      );
      historyPage = page.page;
      historyTotal = page.total;
      historyItems = reset
        ? page.items
        : [
            ...new Map(
              [...historyItems, ...page.items].map((x) => [x.id, x]),
            ).values(),
          ];
    } catch (requestError: unknown) {
      historyError =
        requestError instanceof ApiError
          ? requestError.message
          : "获取核验记录失败";
    } finally {
      historyLoading = false;
    }
  }

  async function submitVerify() {
    const normalized = normalizeTicketCode(ticketCodeInput);
    if (normalized.length === 0) {
      toast.error("请输入票号，或点击上方区域开启扫码");
      return;
    }
    if (!TICKET_CODE_PATTERN.test(normalized)) {
      toast.error("票号格式不正确：应为 20 位字母数字");
      return;
    }

    verifying = true;
    try {
      const ticket = await request<Ticket>(endpoints.ticketVerify(), {
        method: "POST",
        body: { ticketCode: normalized },
      });
      verifiedTicket = ticket;
      ticketCodeInput = normalized;
      // Refresh the persisted history so the record tab stays in sync.
      void loadHistory(true);
      stopCamera();
    } catch (requestError: unknown) {
      // Conflict 409 messages (repeat verification, cancelled booking, ...)
      // come from the backend ready to display, surface them verbatim.
      toast.error(
        requestError instanceof ApiError
          ? requestError.message
          : "核验失败，请稍后重试",
      );
    } finally {
      verifying = false;
    }
  }

  // Clicking the square scan area toggles the camera; every failure surfaces
  // as a toast so the card stays clean.
  function toggleCamera(): void {
    if (isCameraActive) {
      stopCamera();
      return;
    }
    void startCamera();
  }

  async function startCamera(): Promise<void> {
    const detectorConstructor = getBarcodeDetectorConstructor();
    if (detectorConstructor === undefined) {
      cameraState = "unsupported";
      toast.error(
        "当前浏览器不支持摄像头扫码（需要 Barcode Detection API），请手动输入票号。",
      );
      return;
    }
    if (navigator.mediaDevices === undefined) {
      cameraState = "unsupported";
      toast.error("当前环境无法访问摄像头，请手动输入票号。");
      return;
    }

    cameraState = "starting";
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      const element = videoElement;
      if (element !== null) {
        element.srcObject = stream;
        await element.play();
      }
      const detector = new detectorConstructor({ formats: ["qr_code"] });
      scanning = true;
      cameraState = "running";
      void scan(detector);
    } catch (error) {
      cameraState = "idle";
      stopCamera();
      if (error instanceof DOMException) {
        if (
          error.name === "NotAllowedError" ||
          error.name === "SecurityError"
        ) {
          toast.error("摄像头权限被拒绝，请在浏览器地址栏允许摄像头后重试。");
          return;
        }
        if (
          error.name === "NotFoundError" ||
          error.name === "OverconstrainedError"
        ) {
          toast.error("没有找到可用的摄像头，请改用手动输入票号。");
          return;
        }
        if (error.name === "NotReadableError") {
          toast.error("摄像头被其他程序占用，请关闭占用程序后重试。");
          return;
        }
      }
      toast.error("摄像头启动失败，请改用手动输入票号完成核验。");
    }
  }

  function stopCamera(): void {
    scanning = false;
    if (stream !== null) {
      for (const track of stream.getTracks()) {
        track.stop();
      }
      stream = null;
    }
    const element = videoElement;
    if (element !== null) {
      element.srcObject = null;
    }
    if (isCameraActive) {
      cameraState = "idle";
    }
  }

  // Poll the video element with the Barcode Detection API until a valid
  // ticket code is recognized (ticket-qr.md §3.2). Recognition failures stay
  // silent so scanning can continue; only invalid content toasts once.
  async function scan(detector: BarcodeDetectorInstance): Promise<void> {
    while (scanning) {
      const element = videoElement;
      if (element === null) {
        break;
      }
      try {
        const detected = await detector.detect(element);
        const first = detected[0];
        if (first !== undefined) {
          const normalized = normalizeTicketCode(first.rawValue);
          if (TICKET_CODE_PATTERN.test(normalized)) {
            ticketCodeInput = normalized;
            stopCamera();
            await submitVerify();
          } else {
            toast.error("识别到的内容不是有效票号，请对准电子票上的二维码。");
          }
          break;
        }
      } catch {
        // Keep polling; transient frame errors are not user-actionable.
      }
      await new Promise<void>((resolve) => {
        setTimeout(resolve, 250);
      });
    }
  }
</script>

<NavigationLayout {panel} {body} />

{#snippet panel()}
  <Description category="verify" />
{/snippet}

{#snippet body()}
  <div
    class={[
      "sticky",
      "top-14",
      "h-14",
      "px-6",
      "flex",
      "items-center",
      "gap-4",
      "bg-background/80",
      "backdrop-blur-xs",
    ]}
  >
    <div class={["grow", "overflow-x-scroll", "overflow-y-hidden"]}>
      <Tabs.Root bind:value={verifyTab} class={["w-full"]}>
        <Tabs.List>
          <Tabs.Trigger value="verify">核验</Tabs.Trigger>
          <Tabs.Trigger value="history">核验记录</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>
    </div>
  </div>
  {#if verifyTab === "verify"}
    <div class={["px-6", "py-4"]}>
      <Item.Root variant="muted">
        <div
          class={[
            "w-full",
            "py-4",
            "flex",
            "flex-col",
            "gap-4",
            "overflow-hidden",
          ]}
        >
          <Item.Root class={["p-0"]}>
            <Item.Media class={["size-8"]} variant="icon">
              <RiQrScan2Line />
            </Item.Media>
            <Item.Content>
              <Item.Title>扫码核验</Item.Title>
            </Item.Content>
          </Item.Root>
          <button
            type="button"
            class={[
              "aspect-square",
              "w-full",
              "relative",
              "overflow-hidden",
              "rounded-3xl",
              "border",
              "bg-background",
              "cursor-pointer",
            ]}
            onclick={toggleCamera}
          >
            <video
              bind:this={videoElement}
              class={isCameraActive
                ? ["h-full", "w-full", "object-cover"]
                : ["hidden"]}
              autoplay
              playsinline
              muted
            ></video>
            {#if !isCameraActive}
              <div
                class={[
                  "absolute",
                  "inset-0",
                  "flex",
                  "flex-col",
                  "items-center",
                  "justify-center",
                  "gap-2",
                  "text-muted-foreground",
                ]}
              >
                <RiCameraLine class={["size-12"]} />
                <p class={["text-sm"]}>点击开启扫码</p>
              </div>
            {/if}
          </button>
          <div class={["flex", "gap-2"]}>
            <Input
              class={["font-mono"]}
              bind:value={ticketCodeInput}
              autocomplete="off"
              spellcheck={false}
              maxlength={40}
              placeholder="输入 20 位票号"
              disabled={verifying}
            />
            <Button
              size="icon"
              aria-label="确认核销"
              title="确认核销"
              disabled={verifying}
              onclick={() => {
                void submitVerify();
              }}
            >
              <RiCheckLine />
            </Button>
          </div>
        </div>
      </Item.Root>
    </div>
    {#if verifiedTicket}
      <TicketView ticket={verifiedTicket} />
    {/if}
  {:else}
    <div class={["px-2", "py-4", "flex", "flex-col"]}>
      {#each historyItems as ticket (ticket.id)}
        <Item.Root>
          <Item.Content class={["overflow-hidden"]}>
            <Item.Title class={["line-clamp-1"]}>
              {ticket.event.title}
            </Item.Title>
            <Item.Description class={["line-clamp-1"]}>
              <span class={["font-mono"]}>{ticket.ticketCode}</span>
              · {ticket.verifiedAt === null
                ? "—"
                : formatDateTime(ticket.verifiedAt)}
            </Item.Description>
          </Item.Content>
        </Item.Root>
      {/each}
      {#if historyItems.length < historyTotal}
        <Button
          variant="secondary"
          disabled={historyLoading}
          onclick={() => {
            void loadHistory(false);
          }}
        >
          加载更多核验记录
        </Button>
      {/if}
    </div>
  {/if}
{/snippet}
