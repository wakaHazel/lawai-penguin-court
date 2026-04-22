import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

function normalizeBasePath(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    return "/";
  }

  if (trimmed === "/") {
    return "/";
  }

  const withoutEdgeSlashes = trimmed.replace(/^\/+|\/+$/g, "");
  return `/${withoutEdgeSlashes}/`;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");

  return {
    base: normalizeBasePath(env.VITE_BASE_PATH),
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: 4173,
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        },
        "/health": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        },
        "/generated-cg": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        },
        "/generated-cg-library": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        },
      },
    },
  };
});
