import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev-server proxy is only used for `npm run dev` outside Docker.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
