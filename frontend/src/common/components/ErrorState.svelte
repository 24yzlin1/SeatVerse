<script lang="ts">
  const {
    message = "加载失败，请稍后重试",
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
    "text-destructive", // 这里用了破坏色/危险色
    className
  ]}
>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    class={["w-12", "h-12", "mb-4", "opacity-50"]}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
  <span class={["text-sm", "font-medium"]}>{message}</span>
</div>
