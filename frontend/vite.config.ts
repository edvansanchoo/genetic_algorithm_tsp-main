import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // WebSocket goes directly to :8000 in dev (see useWebSocket.ts).
    // Proxying /ws here causes ECONNABORTED with high-frequency state pushes.
  },
  build: {
    outDir: "dist",
  },
});
