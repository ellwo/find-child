import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '');
  const apiBaseUrl = env.VITE_API_BASE_URL || "http://localhost:8000";
  
  return {
    server: {
      host: "::",
      port: 8080,
      proxy: {
        "/api": {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, "/api"),
        },
        "/storage": {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/storage/, "/storage"),
        },
        "/ws/": {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/ws\//, "/ws/"),
        },
      },
    },
    plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
