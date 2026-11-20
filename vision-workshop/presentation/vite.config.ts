import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

// Sunum, proje kökündeki paylaşılan dosyaları (workshop.config.json, shared/) içe aktarır.
const projectRoot = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    host: "localhost",      // kamera erişimi için localhost güvenli bağlam sayılır
    port: 5173,
    fs: { allow: [projectRoot] },
  },
  preview: { host: "localhost", port: 4173 },
  build: { target: "es2022", chunkSizeWarningLimit: 1200 },
});
