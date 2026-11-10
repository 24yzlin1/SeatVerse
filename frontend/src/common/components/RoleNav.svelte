<script lang="ts">
  import { router } from "@/common/router";
  import { auth } from "@/common/stores/auth.svelte";

  interface NavItem {
    label: string;
    path: string;
  }

  /** 未登录时的一项都不给，只留「登录 / 注册」两个动作。 */
  const NO_ITEMS: readonly NavItem[] = [];

  const USER_NAV: readonly NavItem[] = [
    { label: "活动", path: "/events" },
    { label: "我的预约", path: "/bookings" },
  ];

  /** 主办方在普通用户两项之外多一个后台入口。 */
  const ORGANIZER_NAV: readonly NavItem[] = [
    ...USER_NAV,
    { label: "主办方后台", path: "/organizer/events" },
  ];

  const LINK_BASE =
    "rounded-md px-3 py-1.5 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none";
  const LINK_ACTIVE = "bg-accent font-medium text-accent-foreground";
  const LINK_IDLE = "text-muted-foreground hover:bg-accent hover:text-accent-foreground";

  // 首帧与启动回源期间身份还没定：先占位，免得已登录用户闪一下「登录 / 注册」。
  const isPending = $derived(auth.status === "idle" || auth.status === "loading");
  const navItems = $derived(
    auth.isLoggedIn ? (auth.role === "organizer" ? ORGANIZER_NAV : USER_NAV) : NO_ITEMS,
  );
  const userName = $derived(auth.user?.name ?? "");

  /** 子路径也算命中：`/events/9/seats` 高亮「活动」，`/bookings/9/ticket` 高亮「我的预约」。 */
  function isActive(path: string): boolean {
    return router.path === path || router.path.startsWith(`${path}/`);
  }

  function linkClass(path: string): string {
    return `${LINK_BASE} ${isActive(path) ? LINK_ACTIVE : LINK_IDLE}`;
  }

  function handleLogout(): void {
    auth.logout();
  }
</script>

<nav class="flex flex-wrap items-center gap-1 text-sm" aria-label="主导航">
  {#if isPending}
    <span class="sr-only">正在确认登录状态</span>
    <span class="h-7 w-16 animate-pulse rounded-md bg-muted" aria-hidden="true"></span>
    <span class="h-7 w-14 animate-pulse rounded-md bg-muted" aria-hidden="true"></span>
  {:else}
    {#each navItems as item (item.path)}
      <a
        href={`#${item.path}`}
        class={linkClass(item.path)}
        aria-current={isActive(item.path) ? "page" : undefined}
      >
        {item.label}
      </a>
    {/each}

    {#if auth.isLoggedIn}
      {#if userName}
        <span class="hidden px-2 text-muted-foreground sm:inline">{userName}</span>
      {/if}
      <button type="button" class={`${LINK_BASE} ${LINK_IDLE}`} onclick={handleLogout}>
        退出
      </button>
    {:else}
      <a href="#/login" class={linkClass("/login")}>登录</a>
      <a href="#/register" class={linkClass("/register")}>注册</a>
    {/if}
  {/if}
</nav>
