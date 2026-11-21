import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Same-origin proxy to the backend (docs/INTERFACES.md section 1: keep checkout-bearing
// state on loopback). The app calls these paths on its own origin, so no CORS is involved.
const BACKEND = process.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8787";
const routes = ["/state", "/health", "/utterance", "/intent", "/session"];

export default defineConfig({
  plugins: [react()],
  server: { proxy: Object.fromEntries(routes.map((r) => [r, BACKEND])) },
});
