<script lang="ts">
  import { push } from "svelte-spa-router";

  import Error from "@/common/Error.svelte";
</script>

<Error
  title="404"
  description="这个页面可能搬走了，也可能从没存在过。先回首页看看吧。"
  backCallback={() => push("/")}
/>
