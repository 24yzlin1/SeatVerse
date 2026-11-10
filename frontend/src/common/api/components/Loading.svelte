<script lang="ts">
  // 允许外部传入额外的 class，方便在外层调整边距或大小
  const { class: className = "" }: { class?: string } = $props();
</script>

<div
  class={[
    "flex",
    "flex-col",
    "items-center",
    "justify-center",
    "w-full",
    "py-12",
    "text-muted-foreground",
    className
  ]}
>
  <!-- 这是一个标准的 CSS 旋转动画 -->
  <div
    class={[
      "w-8",
      "h-8",
      "mb-4",
      "border-4",
      "border-secondary",
      "border-t-primary",
      "rounded-full",
      "animate-spin"
    ]}
  ></div>
  <span class={["text-sm"]}>加载中...</span>
</div>
