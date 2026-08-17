import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

export default defineConfig({
  plugins: [
    react(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // El frontend de SaludsaActas solo debe ser accesible desde loopback.
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      }
    }
  },
  preview: {
    host: "127.0.0.1",
    port: 5173,
  }
})
