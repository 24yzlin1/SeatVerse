<script module lang="ts">
  import type { Component } from "svelte";
  import { RiTicket2Line } from "remixicon-svelte";

  import * as Empty from "$lib/components/ui/empty";

  export const description: Record<
    string,
    {
      title: string;
      description: string;
      icon: Component;
    }
  > = {
    booking: {
      title: "我的预约",
      description:
        "你抢到的每一张票都收在这里。点开就能看到入场码，到场时出示就行。",
      icon: RiTicket2Line,
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
