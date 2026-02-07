import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: (() => {
          // Backend writes its chosen port here on startup.
          const portFile = path.resolve(__dirname, "../backend/.runtime-port");
          try {
            const raw = fs.readFileSync(portFile, "utf8").trim();
            const port = Number.parseInt(raw, 10);
            if (Number.isFinite(port) && port > 0) return `http://localhost:${port}`;
          } catch (e) {
            // ignore
          }
          // Fallback for first-run before backend has started.
          return "http://localhost:5001";
        })(),
        changeOrigin: true,
      },
    },
  },
});
