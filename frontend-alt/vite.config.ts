import tailwindcss from "@tailwindcss/vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";
import path from "path";

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
