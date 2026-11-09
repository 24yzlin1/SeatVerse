<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { router, setAuthSource } from "@/common/router";
  import RouteView from "@/common/router/RouteView.svelte";
  import { auth } from "@/common/stores/auth.svelte";

  // S2-09 的最小接线 + S2-12 的会话接线。S2-10 会在此基础上加 AppShell。
  onMount(() => {
    // 守卫通过这个接缝读会话，不直接依赖 store（S2-09 预留的 setAuthSource）。
    setAuthSource({
      snapshot: () => auth.snapshot(),
      bootstrap: () => auth.bootstrap(),
    });
    // 先启动回源、再 init；守卫在 status === "idle" 时 await 同一个 in-flight Promise
    // （auth.md §5），因此不会白屏等待网络超时。
    void auth.bootstrap();
    router.init();
  });

  onDestroy(() => {
    router.destroy();
  });
</script>

<RouteView />
