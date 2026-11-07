import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: { "@": path.resolve("./src"), $lib: path.resolve("./src/lib") },
  },
  server: {
    proxy: {
      // 后端源码路由统一带 /api 前缀，代理原样转发、不剥前缀
      "^/api/": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
