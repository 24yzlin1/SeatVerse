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
      "^/api/": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
