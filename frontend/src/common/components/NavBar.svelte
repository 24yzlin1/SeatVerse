<script lang="ts">
  import RoleNav from "./RoleNav.svelte";
</script>

<header class="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
  <div
    class="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8"
  >
    <!-- 站名同时是回首页入口：纯 hash 链接，中键与新标签页也能直接用。 -->
    <a href="#/events" class="rounded text-base font-semibold tracking-tight">
      SeatVerse
    </a>

    <RoleNav />
  </div>
</header>
