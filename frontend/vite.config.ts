import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: true, // Enable source maps for production builds
  },
  css: {
    devSourcemap: true, // Enable CSS source maps in development
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    host: '0.0.0.0',
    proxy: {
      // Use /api prefix for all backend API calls to avoid conflicts with React routes
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        rewrite: (path) => {
          const newPath = path.replace(/^\/api/, '');
          console.log(`🔄 Proxying ${path} to ${newPath}`);
          return newPath;
        }
      }
    },
    // Configure middleware to handle client-side routing
    middlewareMode: false,
  },
  // Ensure proper handling of client-side routes
  appType: 'spa',
});