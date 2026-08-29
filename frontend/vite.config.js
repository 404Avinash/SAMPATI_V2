import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/upi": "http://localhost:8000",
      "/gateway": "http://localhost:8000",
      "/cases": "http://localhost:8000",
      "/stats": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    outDir: "dist",
  },
});
