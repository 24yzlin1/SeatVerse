<script lang="ts">
  interface Props {
    /** 未命中的路径，由 RouteView 传入，用于把 404 指向具体地址。 */
    path?: string;
  }

  const props: Props = $props();
</script>

<div>
  <h1>404 · 页面不存在</h1>
  {#if props.path}
    <p>没有找到 <code>{props.path}</code> 对应的页面，可能是链接失效或输入有误。</p>
  {:else}
    <p>该地址没有对应的页面，可能是链接失效或输入有误。</p>
  {/if}
  <a href="#/events">回活动列表</a>
</div>
