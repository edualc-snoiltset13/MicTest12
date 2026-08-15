import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The dev server proxies /api and the health probes to the FastAPI backend so
// the browser sees a single origin. That keeps the CSP `connect-src 'self'`
// honest in development and means the Cypress suite can intercept requests at
// the same paths it will use in production.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/healthz': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/readyz': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  preview: {
    port: 4173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/healthz': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/readyz': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Locale bundles are split so a viewer only downloads the language
          // they use. Five full locales in the main chunk is ~40 KB of dead
          // weight for a single-language user.
          vendor: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
});
