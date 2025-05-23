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
    proxy: {
      // Direct API routes without the /api prefix
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/texts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/contests': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/votes': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/agents': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Keep compatibility with any code still using the /api prefix
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => {
          const newPath = path.replace(/^\/api/, '');
          console.log(`Proxying ${path} to ${newPath}`);
          return newPath;
        }
      }
    },
  },
}); 