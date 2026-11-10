<script lang="ts">
  import type { Snippet } from "svelte";

  import NavBar from "./NavBar.svelte";

  interface Props {
    /** 内容区，由 App.svelte 传入 <RouteView />。 */
    children: Snippet;
  }

  // 保留 props 对象而不是解构：页面切换时 children 的更新不会丢。
  const props: Props = $props();
</script>

<div class="flex min-h-screen flex-col bg-background text-foreground">
  <NavBar />

  <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
    {@render props.children()}
  </main>

  <footer class="border-t border-border">
    <div
      class="mx-auto w-full max-w-6xl px-4 py-4 text-xs text-muted-foreground sm:px-6 lg:px-8"
    >
      SeatVerse · 座位预约与电子票
    </div>
  </footer>
</div>
