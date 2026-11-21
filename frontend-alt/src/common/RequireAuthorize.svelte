<script lang="ts">
  import { type Component } from "svelte";
  import { RiLock2Line } from "remixicon-svelte";

  import * as Empty from "$lib/components/ui/empty";
  import Button from "$lib/components/ui/button/button.svelte";

  import { authentication } from "@/common/stores/authentication.svelte";
  import type { Role } from "@/common/api";

  // Route wrapper guarding pages that need a session, optionally restricted
  // to specific roles. When the check fails it shows a prompt and opens the
  // login drawer through `showLoginCallback`; otherwise the wrapped page is
  // rendered with the route parameters.
  const {
    target,
    params,
    roles,
    showLoginCallback,
  }: {
    target?: Component;
    params: Record<string, string>;
    roles?: readonly Role[];
    showLoginCallback?: (isShow: boolean) => void;
  } = $props();

  const isPermitted = $derived.by(() => {
    if (!authentication.isLoggedIn) {
      return false;
    }
    if (roles !== undefined && roles.length > 0) {
      const role = authentication.role;
      return role !== null && roles.includes(role);
    }
    return true;
  });
</script>

{#if !authentication.isLoggedIn}
  <Empty.Root class={["h-72"]}>
    <Empty.Header>
      <Empty.Media>
        <div class={["size-12"]}>
          <RiLock2Line />
        </div>
      </Empty.Media>
      <Empty.Title>请先登录</Empty.Title>
      <Empty.Description>
        登录或注册账号后，可以继续访问预约与电子票功能。
      </Empty.Description>
    </Empty.Header>
    <Empty.Content>
      <Button onclick={() => showLoginCallback?.(true)}>登录后继续</Button>
    </Empty.Content>
  </Empty.Root>
{:else if !isPermitted}
  <Empty.Root class={["h-72"]}>
    <Empty.Header>
      <Empty.Media>
        <div class={["size-12"]}>
          <RiLock2Line />
        </div>
      </Empty.Media>
      <Empty.Title>没有权限</Empty.Title>
      <Empty.Description>该页面仅对主办方账号开放。</Empty.Description>
    </Empty.Header>
    <Empty.Content>
      <Button onclick={() => showLoginCallback?.(true)}>切换账号</Button>
    </Empty.Content>
  </Empty.Root>
{:else}
  {@const Target = target}
  <Target {params} />
{/if}
