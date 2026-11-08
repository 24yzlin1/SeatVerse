<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { router } from "@/common/router";
  import RouteView from "@/common/router/RouteView.svelte";

  // S2-09 的最小接线：只挂路由。S2-10 会在此基础上加 AppShell 与 auth.bootstrap()。
  onMount(() => {
    router.init();
  });

  onDestroy(() => {
    router.destroy();
  });
</script>

<RouteView />
