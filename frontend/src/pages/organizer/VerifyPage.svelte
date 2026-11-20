<script lang="ts">
  import { onMount } from "svelte";

  import { ApiError, endpoints, request } from "@/common/api";
  import type { Ticket, TicketStatus } from "@/common/api/types";
  import { router } from "@/common/router";
  import { getBarcodeDetectorConstructor } from "@/common/utils/barcode";
  import type { BarcodeDetectorInstance } from "@/common/utils/barcode";
  import { formatDateTime } from "@/common/utils/datetime";
  import { TICKET_STATUS_LABEL } from "@/common/utils/labels";

  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";

  type CameraState =
    "idle" | "starting" | "running" | "unsupported" | "denied" | "error";

  /** 票号规范形式：20 位 Crockford Base32（ticket-qr.md §2.1）。 */
  const TICKET_CODE_PATTERN = /^[0-9A-HJKMNP-TV-Z]{20}$/;

  const STATUS_BADGE_CLASS: Record<TicketStatus, string[]> = {
    reserved: ["bg-secondary", "text-secondary-foreground"],
    cancelled: ["bg-muted", "text-muted-foreground"],
    used: ["bg-primary", "text-primary-foreground"],
  };

  let code = $state("");
  let inputError = $state("");
  let verifying = $state(false);
  let verifyError = $state("");
  let result = $state<Ticket | null>(null);
  let history = $state<Ticket[]>([]);
  let copyNotice = $state("");

  let cameraState = $state<CameraState>("idle");
  let cameraMessage = $state("");
  let videoElement = $state<HTMLVideoElement | null>(null);

  let stream: MediaStream | null = null;
  let scanning = false;

  const isCameraActive = $derived(
    cameraState === "running" || cameraState === "starting",
  );

  function normalizeTicketCode(value: string): string {
    return value.trim().replace(/-/g, "").toUpperCase();
  }

  function describeError(error: unknown, fallback: string): string {
    return error instanceof ApiError ? error.message : fallback;
  }

  onMount(() => {
    const preset = router.query.get("code");
    if (preset !== null) {
      code = normalizeTicketCode(preset);
    }
    return () => {
      stopCamera();
    };
  });

  async function submit(): Promise<void> {
    inputError = "";
    verifyError = "";
    copyNotice = "";
    result = null;

    const normalized = normalizeTicketCode(code);
    if (normalized.length === 0) {
      inputError = "请输入票号，或使用摄像头扫码";
      return;
    }
    if (!TICKET_CODE_PATTERN.test(normalized)) {
      inputError = "票号格式不正确：应为 20 位字母数字，且不含 I、L、O、U";
      return;
    }

    verifying = true;
    try {
      const ticket = await request<Ticket>(endpoints.ticketVerify(), {
        method: "POST",
        body: { ticketCode: normalized },
      });
      code = normalized;
      result = ticket;
      history = [ticket, ...history].slice(0, 5);
      stopCamera();
    } catch (error) {
      // 409 的 message 由后端给出，重复核验时包含首次核验时间（ticket-qr.md §4.3）。
      verifyError = describeError(error, "核验失败，请稍后重试");
    } finally {
      verifying = false;
    }
  }

  function describeCameraError(error: unknown): {
    state: CameraState;
    message: string;
  } {
    if (error instanceof DOMException) {
      if (error.name === "NotAllowedError" || error.name === "SecurityError") {
        return {
          state: "denied",
          message:
            "摄像头权限被拒绝。请在浏览器地址栏允许摄像头后重试，或直接手动输入票号。",
        };
      }
      if (
        error.name === "NotFoundError" ||
        error.name === "OverconstrainedError"
      ) {
        return {
          state: "error",
          message: "没有找到可用的摄像头，请改用手动输入票号。",
        };
      }
      if (error.name === "NotReadableError") {
        return {
          state: "error",
          message: "摄像头被其他程序占用，请关闭占用程序后重试。",
        };
      }
    }
    return {
      state: "error",
      message: "摄像头启动失败，请改用手动输入票号完成核验。",
    };
  }

  async function startCamera(): Promise<void> {
    cameraMessage = "";
    verifyError = "";
    copyNotice = "";

    const detectorConstructor = getBarcodeDetectorConstructor();
    if (detectorConstructor === undefined) {
      cameraState = "unsupported";
      cameraMessage =
        "当前浏览器不支持摄像头扫码（需要 Barcode Detection API），请手动输入票号。";
      return;
    }
    if (navigator.mediaDevices === undefined) {
      cameraState = "unsupported";
      cameraMessage = "当前环境无法访问摄像头，请手动输入票号。";
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
      const described = describeCameraError(error);
      cameraState = described.state;
      cameraMessage = described.message;
      stopCamera();
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
    if (cameraState === "running" || cameraState === "starting") {
      cameraState = "idle";
    }
  }

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
            code = normalized;
            stopCamera();
            await submit();
          } else {
            cameraMessage =
              "识别到的内容不是有效票号，请对准电子票上的二维码。";
          }
          break;
        }
      } catch {
        cameraMessage = "画面识别失败，请保持二维码在取景框内。";
      }
      await new Promise<void>((resolve) => {
        setTimeout(resolve, 250);
      });
    }
  }

  async function copyCode(ticketCode: string): Promise<void> {
    copyNotice = "";
    try {
      await navigator.clipboard.writeText(ticketCode);
      copyNotice = "票号已复制";
    } catch {
      copyNotice = "复制失败，请手动选中票号复制";
    }
  }

  function resetResult(): void {
    result = null;
    verifyError = "";
    code = "";
    inputError = "";
    copyNotice = "";
  }
</script>

<section class={["flex", "flex-col", "gap-6"]}>
  <header
    class={["flex", "flex-wrap", "items-start", "justify-between", "gap-3"]}
  >
    <div>
      <h1 class={["text-3xl", "font-bold"]}>核验签到</h1>
      <p class={["mt-2", "text-muted-foreground"]}>
        支持摄像头扫码与手动输入两条通道；同一张票只能核验一次。
      </p>
    </div>
    <Button href="#/organizer/events" variant="outline">返回活动管理</Button>
  </header>

  <div class={["grid", "gap-6", "lg:grid-cols-2"]}>
    <div class={["flex", "flex-col", "gap-6"]}>
      <form
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
        onsubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <h2 class={["text-xl", "font-semibold"]}>手动输入票号</h2>
        <p class={["text-xs", "text-muted-foreground"]}>
          支持小写与连字符，提交前会自动归一化为 20 位大写票号。
        </p>

        <div class={["flex", "flex-col", "gap-2"]}>
          <Label for="ticketCode">票号</Label>
          <Input
            id="ticketCode"
            bind:value={code}
            autocomplete="off"
            spellcheck={false}
            maxlength={40}
            placeholder="SV7F3K9Q2M4T8X6B5N2P"
            disabled={verifying}
            class={["font-mono", "tracking-wider"]}
          />
        </div>

        {#if inputError.length > 0}
          <p
            class={["text-sm", "font-medium", "text-destructive"]}
            role="alert"
          >
            {inputError}
          </p>
        {/if}

        <div class={["flex", "flex-wrap", "gap-2"]}>
          <Button type="submit" disabled={verifying}>
            {verifying ? "核验中…" : "核验签到"}
          </Button>
        </div>
      </form>

      <div
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
        <h2 class={["text-xl", "font-semibold"]}>摄像头扫码</h2>
        <p class={["text-xs", "text-muted-foreground"]}>
          需要浏览器支持 Barcode Detection API
          并允许摄像头；不可用时请使用上面的手动通道。
        </p>

        <div
          class={[
            "overflow-hidden",
            "rounded-xl",
            "border",
            "border-border",
            "bg-muted",
          ]}
        >
          <video
            bind:this={videoElement}
            class={isCameraActive
              ? ["h-56", "w-full", "object-cover"]
              : ["hidden"]}
            autoplay
            playsinline
            muted
          ></video>
          {#if !isCameraActive}
            <div
              class={[
                "flex",
                "h-56",
                "items-center",
                "justify-center",
                "text-sm",
                "text-muted-foreground",
              ]}
            >
              摄像头未开启
            </div>
          {/if}
        </div>

        {#if cameraMessage.length > 0}
          <p class={["text-sm", "text-muted-foreground"]} role="status">
            {cameraMessage}
          </p>
        {/if}

        <div class={["flex", "flex-wrap", "gap-2"]}>
          {#if cameraState === "running"}
            <Button variant="outline" onclick={stopCamera}>停止扫码</Button>
          {:else}
            <Button
              variant="outline"
              onclick={() => {
                void startCamera();
              }}
              disabled={cameraState === "starting" || verifying}
            >
              {cameraState === "starting" ? "正在启动…" : "开启摄像头扫码"}
            </Button>
          {/if}
        </div>
      </div>
    </div>

    <div class={["flex", "flex-col", "gap-6"]}>
      {#if verifyError.length > 0}
        <div
          class={[
            "rounded-xl",
            "border",
            "border-destructive/40",
            "bg-destructive/5",
            "p-6",
          ]}
          role="alert"
        >
          <h2 class={["text-lg", "font-semibold", "text-destructive"]}>
            核验未通过
          </h2>
          <p class={["mt-2", "text-sm", "text-destructive"]}>{verifyError}</p>
          <p class={["mt-3", "text-xs", "text-muted-foreground"]}>
            重复核验会返回首次核验时间；已取消预约、已取消或已结束活动均不能签到。
          </p>
        </div>
      {/if}

      {#if result !== null}
        <div
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
          <div
            class={[
              "flex",
              "flex-wrap",
              "items-center",
              "justify-between",
              "gap-2",
            ]}
          >
            <h2 class={["text-xl", "font-semibold"]}>核验成功</h2>
            <span
              class={[
                "rounded-full",
                "px-3",
                "py-1",
                "text-xs",
                "font-medium",
                ...STATUS_BADGE_CLASS[result.status],
              ]}
            >
              {TICKET_STATUS_LABEL[result.status]}
            </span>
          </div>

          <dl class={["grid", "gap-3", "text-sm"]}>
            <div>
              <dt class={["text-xs", "text-muted-foreground"]}>活动</dt>
              <dd>{result.event.title}</dd>
            </div>
            <div>
              <dt class={["text-xs", "text-muted-foreground"]}>场馆与时间</dt>
              <dd>
                {result.event.venue.name} · {formatDateTime(
                  result.event.startTime,
                )} 起
              </dd>
            </div>
            <div>
              <dt class={["text-xs", "text-muted-foreground"]}>座位</dt>
              <dd>{result.seats.map((seat) => seat.label).join("、")}</dd>
            </div>
            <div>
              <dt class={["text-xs", "text-muted-foreground"]}>票号</dt>
              <dd class={["font-mono", "tracking-wider"]}>
                {result.ticketCode}
              </dd>
            </div>
            <div>
              <dt class={["text-xs", "text-muted-foreground"]}>核验时间</dt>
              <dd>
                {result.verifiedAt === null
                  ? "—"
                  : formatDateTime(result.verifiedAt)}
              </dd>
            </div>
          </dl>

          <div class={["flex", "flex-wrap", "gap-2"]}>
            <Button
              variant="outline"
              onclick={() => {
                if (result !== null) {
                  void copyCode(result.ticketCode);
                }
              }}
            >
              复制票号
            </Button>
            <Button onclick={resetResult}>继续核验下一张</Button>
          </div>

          {#if copyNotice.length > 0}
            <p class={["text-xs", "text-muted-foreground"]} role="status">
              {copyNotice}
            </p>
          {/if}
        </div>
      {/if}

      <div
        class={[
          "flex",
          "flex-col",
          "gap-3",
          "rounded-xl",
          "border",
          "border-border",
          "bg-card",
          "p-6",
        ]}
      >
        <h2 class={["text-xl", "font-semibold"]}>本次核验记录</h2>
        {#if history.length === 0}
          <p class={["text-sm", "text-muted-foreground"]}>还没有核验记录。</p>
        {:else}
          <ul class={["flex", "flex-col", "gap-2", "text-sm"]}>
            {#each history as item (item.id)}
              <li
                class={[
                  "flex",
                  "flex-wrap",
                  "items-center",
                  "justify-between",
                  "gap-2",
                ]}
              >
                <span class={["font-mono", "text-xs"]}>{item.ticketCode}</span>
                <span class={["text-xs", "text-muted-foreground"]}>
                  {item.event.title} · {item.verifiedAt === null
                    ? "—"
                    : formatDateTime(item.verifiedAt)}
                </span>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
    </div>
  </div>
</section>
