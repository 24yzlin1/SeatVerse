<script lang="ts">
  import { toast } from "svelte-sonner";
  import { RiLoader4Line } from "remixicon-svelte";

  import { Button } from "$lib/components/ui/button";
  import * as Drawer from "$lib/components/ui/drawer";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import * as Tabs from "$lib/components/ui/tabs";

  import { endpoints, request, ApiError } from "@/common/api";
  import type { LoginResponse } from "@/common/api";
  import { authentication } from "@/common/stores/authentication.svelte";

  // Login and registration drawer content, shown when no session is active.
  // `succeedCallback` closes the drawer after a successful login or
  // registration.
  const { succeedCallback }: { succeedCallback: () => void } = $props();

  let accountTabOption = $state("login");

  let name = $state("");
  let email = $state("");
  let password = $state("");
  let isLoading = $state(false);

  function handleLogin(): void {
    isLoading = true;
    authentication
      .login({ email, password })
      .then(() => {
        toast.success("登录成功");
        succeedCallback();
      })
      .catch((error: unknown) => {
        toast.error(
          error instanceof ApiError ? error.message : "网络异常，请稍后重试",
        );
      })
      .finally(() => (isLoading = false));
  }

  function handleRegister(): void {
    isLoading = true;
    request<LoginResponse>(endpoints.authenticationRegister(), {
      method: "POST",
      body: { name, email, password },
    })
      .then((result) => {
        authentication.setSession(result.token, result.user);
        toast.success("注册成功");
        succeedCallback();
      })
      .catch((error: unknown) => {
        toast.error(
          error instanceof ApiError ? error.message : "网络异常，请稍后重试",
        );
      })
      .finally(() => (isLoading = false));
  }
</script>

<Drawer.Title class={["px-4", "py-8"]}>
  <Tabs.Root bind:value={accountTabOption}>
    <Tabs.List>
      <Tabs.Trigger value="login">登录</Tabs.Trigger>
      <Tabs.Trigger value="register">注册</Tabs.Trigger>
    </Tabs.List>
  </Tabs.Root>
</Drawer.Title>
{#if accountTabOption === "login"}
  <div class={["h-full", "px-4"]}>
    <div class={["flex", "flex-col", "gap-3", "w-full"]}>
      <div class={["flex", "flex-col", "gap-3"]}>
        <Label for="email">邮箱</Label>
        <Input
          id="email"
          type="email"
          bind:value={email}
          disabled={isLoading}
        />
      </div>
      <div class={["flex", "flex-col", "gap-3"]}>
        <Label for="password">密码</Label>
        <Input
          id="password"
          type="password"
          bind:value={password}
          disabled={isLoading}
        />
      </div>
    </div>
  </div>
  <Drawer.Footer class={["px-4", "py-8"]}>
    <Button
      disabled={isLoading}
      onclick={() => {
        handleLogin();
      }}
    >
      {#if isLoading}
        <RiLoader4Line class={["animate-spin"]} />
      {/if}
      登录
    </Button>
  </Drawer.Footer>
{/if}
{#if accountTabOption === "register"}
  <div class={["h-full", "px-4"]}>
    <div class={["flex", "flex-col", "gap-3", "w-full"]}>
      <div class={["flex", "flex-col", "gap-3"]}>
        <Label for="name">用户名</Label>
        <Input id="name" bind:value={name} disabled={isLoading} />
      </div>
      <div class={["flex", "flex-col", "gap-3"]}>
        <Label for="email">邮箱</Label>
        <Input
          id="email"
          type="email"
          bind:value={email}
          disabled={isLoading}
        />
      </div>
      <div class={["flex", "flex-col", "gap-3"]}>
        <Label for="password">密码</Label>
        <Input
          id="password"
          type="password"
          bind:value={password}
          disabled={isLoading}
        />
      </div>
    </div>
  </div>
  <Drawer.Footer class={["px-4", "py-8"]}>
    <Button
      disabled={isLoading}
      onclick={() => {
        handleRegister();
      }}
    >
      {#if isLoading}
        <RiLoader4Line class={["animate-spin"]} />
      {/if}
      注册
    </Button>
  </Drawer.Footer>
{/if}
