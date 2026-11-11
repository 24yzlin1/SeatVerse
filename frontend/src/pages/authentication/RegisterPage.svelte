<script lang="ts">
  import { request, endpoints, ApiError } from "@/common/api";
  import type { LoginResponse } from "@/common/api/types";
  import { auth } from "@/common/stores/auth.svelte";
  import { router } from "@/common/router";
  import { HOME_BY_ROLE } from "@/common/router/routes";

  let username = $state("");
  let password = $state("");
  let confirmPassword = $state("");
  let isLoading = $state(false);
  let errorMessage = $state("");

  async function handleRegister(e: SubmitEvent) {
    e.preventDefault();
    errorMessage = "";

    if (!username.trim() || !password.trim()) {
      errorMessage = "请输入用户名和密码";
      return;
    }
    
    if (password !== confirmPassword) {
      errorMessage = "两次输入的密码不一致";
      return;
    }

    isLoading = true;
    try {
      const res = await request<LoginResponse>("/authentication/register", {
        method: "POST",
        body: { username, password }
      });

      auth.setSession(res.token, res.user);
      
      const role = auth.role;
      if (role) {
        router.navigate(HOME_BY_ROLE[role]);
      } else {
        router.navigate("/events");
      }
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        errorMessage = error.message;
      } else {
        errorMessage = "网络异常，请稍后重试";
      }
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

    <form on:submit={handleRegister} class={["flex", "flex-col", "gap-4"]}>
      <div class={["flex", "flex-col", "gap-2"]}>
        <label for="username" class={["text-sm", "font-medium", "text-foreground"]}>用户名</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          disabled={isLoading}
          placeholder="请输入用户名"
          class={[
            "flex", "h-10", "w-full", "rounded-md", "border", "border-input",
            "bg-transparent", "px-3", "py-2", "text-sm", "text-foreground",
            "focus-visible:outline-none", "focus-visible:ring-2", "focus-visible:ring-ring",
            "disabled:cursor-not-allowed", "disabled:opacity-50"
          ]}
        />
      </div>

      <div class={["flex", "flex-col", "gap-2"]}>
        <label for="password" class={["text-sm", "font-medium", "text-foreground"]}>密码</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          disabled={isLoading}
          placeholder="请输入密码"
          class={[
            "flex", "h-10", "w-full", "rounded-md", "border", "border-input",
            "bg-transparent", "px-3", "py-2", "text-sm", "text-foreground",
            "focus-visible:outline-none", "focus-visible:ring-2", "focus-visible:ring-ring",
            "disabled:cursor-not-allowed", "disabled:opacity-50"
          ]}
        />
      </div>

      <div class={["flex", "flex-col", "gap-2"]}>
        <label for="confirmPassword" class={["text-sm", "font-medium", "text-foreground"]}>确认密码</label>
        <input
          id="confirmPassword"
          type="password"
          bind:value={confirmPassword}
          disabled={isLoading}
          placeholder="请再次输入密码"
          class={[
            "flex", "h-10", "w-full", "rounded-md", "border", "border-input",
            "bg-transparent", "px-3", "py-2", "text-sm", "text-foreground",
            "focus-visible:outline-none", "focus-visible:ring-2", "focus-visible:ring-ring",
            "disabled:cursor-not-allowed", "disabled:opacity-50"
          ]}
        />
      </div>

      {#if errorMessage}
        <div class={["text-sm", "text-destructive", "font-medium", "mt-1"]}>
          {errorMessage}
        </div>
      {/if}

      <button
        type="submit"
        disabled={isLoading}
        class={[
          "inline-flex", "items-center", "justify-center", "rounded-md",
          "text-sm", "font-medium", "h-10", "px-4", "py-2", "w-full", "mt-4",
          "bg-primary", "text-primary-foreground", "hover:bg-primary/90",
          "disabled:pointer-events-none", "disabled:opacity-50"
        ]}
      >
        {isLoading ? "注册中..." : "注册"}
      </button>
    </form>
    
    <div class={["mt-6", "text-center", "text-sm", "text-muted-foreground"]}>
      已有账号？
      <a href="#/login" class={["text-primary", "hover:underline"]}>返回登录</a>
    </div>

  </div>
</div>