<script lang="ts">
  import NotFound from "@/common/components/NotFound.svelte";
  import { router } from "./router.svelte";

  /** `*` 兜底路由不带组件，404 由下面单独分支渲染，以便把失败路径传给页面。 */
  const page = $derived(router.matched?.component ?? null);
</script>

{#if router.isNotFound}
  <NotFound path={router.path} />
{:else if page !== null}
  {@const Page = page}
  <Page />
{:else if router.initialized}
  <NotFound path={router.path} />
{/if}
