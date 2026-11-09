<script lang="ts">
  // 允许外部传入提示文字和额外 class
  let {
    message = "暂无数据",
    class: className = ""
  }: { message?: string; class?: string } = $props();
</script>

<div
  class={[
    "flex",
    "flex-col",
    "items-center",
    "justify-center",
    "w-full",
    "py-16",
    "text-muted-foreground",
    className
  ]}
>
  <!-- 简单用一个 SVG 占位，表示空状态 -->
  <svg
    xmlns="http://www.w3.org/2000/svg"
    class={["w-12", "h-12", "mb-4", "opacity-20"]}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
    />
  </svg>
  <span class={["text-sm"]}>{message}</span>
</div>