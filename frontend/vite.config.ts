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
      // ONLY proxy actual API endpoints, NOT React routes
      // Authentication API
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // User API (but NOT /users page route)
      '^/users$': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/users\\?': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/users/\\d+': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Text API
      '/texts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Contest API
      '/contests': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Votes API
      '/votes': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Dashboard API (but NOT /dashboard page route)
      '^/dashboard/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Agents API (but NOT /agents page route)
      '^/agents$': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/agents\\?': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/agents/\\d+': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Admin API endpoints ONLY - very specific patterns
      '/admin/ai-debug-logs/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('🔄 Proxying debug logs API request:', req.url);
          });
          proxy.on('error', (err, req, res) => {
            console.error('❌ Proxy error for debug logs:', err);
          });
        },
      },
      '^/admin/users$': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/admin/users\\?': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/admin/users/\\d+': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/admin/credits': {
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