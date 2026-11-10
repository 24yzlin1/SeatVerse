<script lang="ts">
  interface Props {
    /** 未命中的路径，由 RouteView 传入，用于把 404 指向具体地址。 */
    path?: string;
  }

  // 保留 props 对象：在两个 404 之间切换路径时，文案要跟着更新。
  const props: Props = $props();
</script>

<div class="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-center">
  <p class="text-5xl font-semibold tracking-tight">404</p>
  <h1 class="text-lg font-medium">页面不存在</h1>

  {#if props.path}
    <p class="max-w-md text-sm text-muted-foreground">
      没有找到 <code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{props.path}</code>
      对应的页面，可能是链接失效或输入有误。
    </p>
  {:else}
    <p class="max-w-md text-sm text-muted-foreground">
      该地址没有对应的页面，可能是链接失效或输入有误。
    </p>
  {/if}

  <a
    href="#/events"
    class="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
  >
    回活动列表
  </a>
</div>
