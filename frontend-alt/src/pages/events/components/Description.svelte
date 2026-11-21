<script module lang="ts">
  import type { Component } from "svelte";
  import { RiCalendarLine } from "remixicon-svelte";

  import * as Empty from "$lib/components/ui/empty";

  export const description: Record<
    string,
    {
      title: string;
      description: string;
      icon: Component;
    }
  > = {
    event: {
      title: "校园活动",
      description:
        "讲座、演出、社团夜……全校的活动都排在这里。挑一场感兴趣的，选好座位，到时候直接到场。",
      icon: RiCalendarLine,
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
