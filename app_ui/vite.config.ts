import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build straight into the FastAPI app's static folder; proxy /api to the local backend in dev.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../app/static", emptyOutDir: true, chunkSizeWarningLimit: 2500 },
  server: { port: 5173, proxy: { "/api": "http://localhost:8765" } },
});
