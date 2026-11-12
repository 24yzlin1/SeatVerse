<script lang="ts">
  import { request, ApiError } from "@/common/api";
  import type { LoginResponse } from "@/common/api/types";
  import { auth } from "@/common/stores/auth.svelte";
  import { router } from "@/common/router";
  import { HOME_BY_ROLE } from "@/common/router/routes";

  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";

  let name = $state("");
  let email = $state("");
  let password = $state("");
  let isLoading = $state(false);
  let errorMessage = $state("");

  async function handleRegister(e: SubmitEvent) {
    e.preventDefault();
    errorMessage = "";

    if (!name.trim() || !email.trim() || !password.trim()) {
      errorMessage = "请填写所有必填项";
      return;
    }

    isLoading = true;
    try {
      const res = await request<LoginResponse>("/authentication/register", {
        method: "POST",
        body: { name, email, password }
      });

      auth.setSession(res.token, res.user);
      const role = auth.role;
      router.navigate(role ? HOME_BY_ROLE[role] : "/events");
    } catch (error: unknown) {
      errorMessage = error instanceof ApiError ? error.message : "网络异常，请稍后重试";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class={["min-h-[70vh]", "flex", "items-center", "justify-center"]}>
  <div class={["w-full", "max-w-md", "p-8", "bg-card", "rounded-xl", "border", "border-border", "shadow-sm"]}>
    <div class={["text-center", "mb-8"]}>
      <h1 class={["text-2xl", "font-bold", "text-foreground", "mb-2"]}>注册 SeatVerse</h1>
      <p class={["text-sm", "text-muted-foreground"]}>创建账号，开始预约</p>
    </div>

    <form onsubmit={handleRegister} class={["flex", "flex-col", "gap-4"]}>
      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="name">用户名</Label>
        <Input id="name" bind:value={name} disabled={isLoading} placeholder="请输入用户名" />
      </div>

      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="email">邮箱</Label>
        <Input id="email" type="email" bind:value={email} disabled={isLoading} placeholder="请输入邮箱" />
      </div>

      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="password">密码</Label>
        <Input id="password" type="password" bind:value={password} disabled={isLoading} placeholder="请输入密码" />
      </div>

      {#if errorMessage}
        <div class={["text-sm", "text-destructive", "font-medium", "mt-1"]}>{errorMessage}</div>
      {/if}

      <Button type="submit" disabled={isLoading} class={["w-full", "mt-4"]}>
        {isLoading ? "注册中..." : "注册"}
      </Button>
    </form>
    
    <div class={["mt-6", "text-center", "text-sm", "text-muted-foreground"]}>
      已有账号？
      <a href="#/login" class={["text-primary", "hover:underline"]}>返回登录</a>
    </div>
  </div>
</div>