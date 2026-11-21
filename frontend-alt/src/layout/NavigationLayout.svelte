<script lang="ts">
  import type { Snippet } from "svelte";

  const {
    panel,
    body,
  }: {
    panel?: Snippet;
    body?: Snippet;
  } = $props();
</script>

<div>
  <div>
    <div>
      {@render panel?.()}
    </div>
  </div>
  <div>
    {@render body?.()}
  </div>
</div>
