<script module lang="ts">
  import type { Component } from "svelte";
  import {
    RiCalendarEventLine,
    RiFileList2Line,
    RiQrScan2Line,
  } from "remixicon-svelte";

  import * as Empty from "$lib/components/ui/empty";

  export const description: Record<
    string,
    {
      title: string;
      description: string;
      icon: Component;
    }
  > = {
    events: {
      title: "后台活动",
      description: "你发起的活动都在这里。新建、发布、停约、看名单，一页搞定。",
      icon: RiCalendarEventLine,
    },
    bookings: {
      title: "活动名单",
      description: "谁约了哪座、来没来，一目了然。现场签到请到签到核验页处理。",
      icon: RiFileList2Line,
    },
    verify: {
      title: "签到核验",
      description:
        "扫一下观众票上的码就完成签到。一张票只能用一次，重复扫码会告诉你第一次是什么时候核的。",
      icon: RiQrScan2Line,
    },
  };
</script>

<script lang="ts">
  const { category }: { category: string } = $props();
</script>

{@render card(
  description[category].title,
  description[category].description,
  description[category].icon,
)}

{#snippet card(title: string, text: string, icon: Component)}
  {@const Icon = icon}
  <Empty.Root class={["h-72"]}>
    <Empty.Header>
      <Empty.Media>
        <div class={["size-12"]}>
          <Icon />
        </div>
      </Empty.Media>
      <Empty.Title>{title}</Empty.Title>
      <Empty.Description>
        {text}
      </Empty.Description>
    </Empty.Header>
  </Empty.Root>
{/snippet}
