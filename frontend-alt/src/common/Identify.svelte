<script lang="ts">
  import { RiMailLine } from "remixicon-svelte";

  import * as Avatar from "$lib/components/ui/avatar";
  import Button from "$lib/components/ui/button/button.svelte";
  import * as Drawer from "$lib/components/ui/drawer";
  import * as Item from "$lib/components/ui/item";

  import { authentication } from "@/common/stores/authentication.svelte";

  // Profile drawer content, shown when a session is active. `succeedCallback`
  // closes the drawer after signing out.
  const { succeedCallback }: { succeedCallback: () => void } = $props();
</script>

<Drawer.Title class={["px-4", "py-8"]}>
  <Item.Root variant="muted">
    <Item.Media variant="image">
      <Avatar.Root size="lg">
        <Avatar.Fallback>
          {authentication.user?.name.charAt(0).toUpperCase()}
        </Avatar.Fallback>
      </Avatar.Root>
    </Item.Media>
    <Item.Title>{authentication.user?.name}</Item.Title>
  </Item.Root>
</Drawer.Title>
<div class={["h-full", "px-4", "flex", "flex-col", "gap-2"]}>
  <Item.Item class={["click-link", "p-0"]}>
    <Item.Media class={["size-8"]}>
      <RiMailLine class={["size-4"]} />
    </Item.Media>
    <Item.Content>
      <Item.Title>{authentication.user?.email ?? "未知"}</Item.Title>
    </Item.Content>
  </Item.Item>
</div>
<Drawer.Footer class={["px-4", "py-8"]}>
  <Button
    onclick={() => {
      authentication.logout();
      succeedCallback();
    }}
    >登出
  </Button>
</Drawer.Footer>
