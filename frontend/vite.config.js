import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://beerfinder-api-877162996755.us-central1.run.app',
        changeOrigin: true,
        secure: false
      },
    },
  },
  build: {
    // Add environment variables to be replaced at build time
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify('https://beerfinder-api-877162996755.us-central1.run.app'),
    },
  },
});
