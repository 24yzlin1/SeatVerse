<script lang="ts">
  import { auth } from "@/common/stores/auth.svelte";
  import { router } from "@/common/router";
  import { ApiError } from "@/common/api";
  import { HOME_BY_ROLE } from "@/common/router/routes";
  
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";

  let email = $state("");
  let password = $state("");
  let isLoading = $state(false);
  let errorMessage = $state("");

  async function handleLogin(e: SubmitEvent) {
    e.preventDefault();
    errorMessage = "";

    if (!email.trim() || !password.trim()) {
      errorMessage = "请输入邮箱和密码";
      return;
    }

    isLoading = true;
    try {
      await auth.login({ email, password });
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
      <h1 class={["text-2xl", "font-bold", "text-foreground", "mb-2"]}>登录 SeatVerse</h1>
      <p class={["text-sm", "text-muted-foreground"]}>进入 3D 场馆，选择你的专属座位</p>
    </div>

    <form onsubmit={handleLogin} class={["flex", "flex-col", "gap-4"]}>
      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="email">邮箱</Label>
        <Input id="email" bind:value={email} disabled={isLoading} placeholder="请输入邮箱" />
      </div>

      <div class={["flex", "flex-col", "gap-2"]}>
        <Label for="password">密码</Label>
        <Input id="password" type="password" bind:value={password} disabled={isLoading} placeholder="请输入密码" />
      </div>

      {#if errorMessage}
        <div class={["text-sm", "text-destructive", "font-medium", "mt-1"]}>{errorMessage}</div>
      {/if}

      <Button type="submit" disabled={isLoading} class={["w-full", "mt-4"]}>
        {isLoading ? "登录中..." : "登录"}
      </Button>
    </form>
    
    <div class={["mt-6", "text-center", "text-sm", "text-muted-foreground"]}>
      还没有账号？
      <a href="#/register" class={["text-primary", "hover:underline"]}>立即注册</a>
    </div>
  </div>
</div>