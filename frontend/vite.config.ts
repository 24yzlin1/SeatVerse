import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

// 后端源码路由统一带 /api 前缀，代理原样转发、不剥前缀（api.md §1）。
// dev 与 preview 共用同一份配置：preview 没有 proxy 时，演示用 preview 会全 404。
const apiProxy = {
  "^/api/": {
    target: "http://localhost:8000",
    changeOrigin: true,
  },
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: { "@": path.resolve("./src"), $lib: path.resolve("./src/lib") },
  },
  server: {
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
});
