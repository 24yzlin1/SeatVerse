<script lang="ts">
  import { pop } from "svelte-spa-router";
  import { RiPlanetLine } from "remixicon-svelte";

  import { Button } from "$lib/components/ui/button";
  import * as Empty from "$lib/components/ui/empty";

  // Shared error display. `title` and `description` describe the failure;
  // both actions are always available: go back, or reload the page.
  const {
    title = "出了点问题",
    description,
    backCallback = pop,
    reloadCallback = () => window.location.reload(),
  }: {
    title?: string;
    description?: string;
    backCallback?: () => void;
    reloadCallback?: () => void;
  } = $props();
</script>

<Empty.Root class={["h-72"]}>
  <Empty.Header>
    <Empty.Media>
      <div class={["size-12"]}>
        <RiPlanetLine />
      </div>
    </Empty.Media>
    <Empty.Title>{title}</Empty.Title>
    <Empty.Description>{description}</Empty.Description>
  </Empty.Header>
  <Empty.Content class={["flex-row", "justify-center"]}>
    <Button onclick={backCallback} variant="secondary" class={["w-24"]}>
      返回
    </Button>
    <Button onclick={reloadCallback} class={["w-24"]}>重新加载</Button>
  </Empty.Content>
</Empty.Root>
