import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5000,
    host: "0.0.0.0",
    allowedHosts: true,
    historyApiFallback: {
      rewrites: [
        { from: /^\/login/, to: "/react.html" },
        { from: /^\/signup/, to: "/react.html" },
        { from: /^\/dashboard/, to: "/react.html" },
      ],
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, "index.html"),
        app: path.resolve(__dirname, "react.html"),
      },
    },
  },
});

