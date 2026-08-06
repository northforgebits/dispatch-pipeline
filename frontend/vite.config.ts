import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies API calls to the FastAPI app so no CORS config is
// needed in either environment. In production the built files in dist/
// are served by FastAPI itself, so requests are same-origin there too.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/records": "http://localhost:8000",
      "/pipeline": "http://localhost:8000",
      "/stats": "http://localhost:8000",
    },
  },
});