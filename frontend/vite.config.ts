/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 서버에서 /api 요청을 백엔드로 프록시합니다.
const backendTarget = process.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    css: false,
    server: {
      deps: {
        inline: [/@fluentui/, /@griffel/, "tabster", "keyborg"],
      },
    },
  },
});
