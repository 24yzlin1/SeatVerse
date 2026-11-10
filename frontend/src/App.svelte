<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { endpoints, request } from "@/common/api";
  import type { LoginResponse, User } from "@/common/api/types";
  import AppShell from "@/common/components/AppShell.svelte";
  import { router, setAuthSource } from "@/common/router";
  import RouteView from "@/common/router/RouteView.svelte";
  import { auth, setAuthApi } from "@/common/stores/auth.svelte";

  // 样式入口只在 main.ts 里 import 一次，这里不再重复引入，避免样式重复注入。

  // 路由、会话与请求层在此接线；应用壳只负责 header + main + footer 的外框。
  onMount(() => {
    // 认证的两个调用统一走 client（令牌注入与 401 处理只在 client 里发生）。
    setAuthApi({
      me: () => request<User>(endpoints.authMe()),
      login: (payload) =>
        request<LoginResponse>(endpoints.authLogin(), { method: "POST", body: payload }),
    });
    // 守卫通过这个接缝读会话，不直接依赖 store（setAuthSource 由路由层提供）。
    setAuthSource({
      snapshot: () => auth.snapshot(),
      bootstrap: () => auth.bootstrap(),
    });
    // 先启动回源、再 init；守卫在身份未定（idle / loading）时 await 同一个 in-flight
    // Promise，因此不会白屏等待网络超时。
    void auth.bootstrap();
    router.init();
  });

  onDestroy(() => {
    router.destroy();
  });
</script>

<AppShell>
  <RouteView />
</AppShell>
