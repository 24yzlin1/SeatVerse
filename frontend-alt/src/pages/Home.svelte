<script>
  import { push } from "svelte-spa-router";

  import * as Avatar from "$lib/components/ui/avatar";
  import Badge from "$lib/components/ui/badge/badge.svelte";
  import Button from "@/lib/components/ui/button/button.svelte";
  import * as Item from "$lib/components/ui/item";
  import { RiArrowRightLine } from "remixicon-svelte";

  const bookingSteps = [
    {
      name: "浏览活动",
      description: "在活动列表中找到感兴趣的活动，查看详情与时间安排。",
      code: "1",
    },
    {
      name: "选择座位",
      description: "在座位图中挑选想要的座位，提交后立即锁定名额。",
      code: "2",
    },
    {
      name: "出示电子票",
      description: "预约成功后在我的预约中出示电子票，现场扫码核验入场。",
      code: "3",
    },
  ];
</script>

<div
  class={[
    "flex",
    "flex-col",
    "gap-4",
    "px-6",
    "pt-20",
    "pb-8",
    "text-center",
    "bg-muted",
    "h-[50vh]",
  ]}
>
  <p
    class={[
      "text-primary",
      "text-4xl",
      "font-semibold",
      "tracking-tight",
      "text-balance",
      "text-left",
    ]}
  >
    欢迎来到 SeatVerse
  </p>
  <p class={["text-foreground", "text-base", "text-balance", "text-left"]}>
    一站式座位预约与电子票平台。浏览校园活动、挑选心仪座位、凭电子票扫码入场，
    每一场活动都能轻松赴约。
  </p>
</div>
<div class={["clip", "content-['']", "block", "h-12", "bg-muted"]}></div>

<div class={["flex", "flex-col", "gap-4", "px-6", "py-8", "text-center"]}>
  <p
    class={[
      "text-primary",
      "text-2xl",
      "font-semibold",
      "tracking-tight",
      "text-balance",
      "text-left",
    ]}
  >
    你的专属座位，一键预约
  </p>
  <p class={["text-foreground", "text-base", "text-balance", "text-left"]}>
    SeatVerse
    提供实时座位图与余座状态，预约成功自动生成电子票，入场时扫码即可完成核验，全程无需排队。
  </p>
  <div class={["flex", "gap-2"]}>
    {#each ["3D 选座", "实时余座", "电子票", "扫码核验"] as badgeLabel}
      <Badge variant="secondary">{badgeLabel}</Badge>
    {/each}
  </div>
  <Button class={["w-[50%]"]} size="lg" onclick={() => push("/events")}>
    立即浏览活动
    <RiArrowRightLine />
  </Button>
</div>

<div class={["flex", "flex-col", "gap-2", "py-8"]}>
  <div class={["flex", "flex-col", "gap-4", "px-6", "text-center"]}>
    <p
      class={[
        "text-primary",
        "text-2xl",
        "font-semibold",
        "tracking-tight",
        "text-balance",
        "text-left",
      ]}
    >
      三步完成预约
    </p>
    <p class={["text-foreground", "text-base", "text-balance", "text-left"]}>
      从浏览活动到扫码入场，整个流程一气呵成，简单直观。
    </p>
  </div>
  <div class={["px-2"]}>
    {#each bookingSteps as { name, description, code }}
      <Item.Root class={["click-link"]}>
        <Item.Media class={["size-8"]}>
          <Avatar.Root class="rounded-lg">
            <Avatar.Fallback>{code}</Avatar.Fallback>
          </Avatar.Root>
        </Item.Media>
        <Item.Content>
          <Item.Title class={["line-clamp-1"]}>
            {name}
          </Item.Title>
          <Item.Description class={["line-clamp-1"]}>
            {description}
          </Item.Description>
        </Item.Content>
      </Item.Root>
    {/each}
  </div>
</div>

<style>
  .clip {
    clip-path: polygon(
      0% 60%,
      25% 60%,
      25% 100%,
      60% 100%,
      60% 50%,
      80% 50%,
      80% 0,
      0 0
    );
  }
</style>
