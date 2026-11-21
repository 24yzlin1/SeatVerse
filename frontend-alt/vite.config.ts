import tailwindcss from "@tailwindcss/vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";
import path from "path";
import { layerchartLifecycle } from "./vite.plugins/layerchart-lifecycle.ts";

const apiProxy = {
  "^/api/": {
    target: "http://localhost:8000",
    changeOrigin: true,
  },
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [layerchartLifecycle(), tailwindcss(), svelte()],
  optimizeDeps: {
    // Keep the lifecycle fix in the normal transform pipeline in dev and build.
    exclude: ["layerchart"],
  },
  resolve: {
    alias: {
      "@": path.resolve("./src"),
      $lib: path.resolve("./src/lib"),
    },
  },
  server: {
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
});
