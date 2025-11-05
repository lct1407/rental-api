import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split React and React DOM into their own chunk
          'react-vendor': ['react', 'react-dom'],
          // Split React Router into its own chunk
          'router': ['react-router-dom'],
          // Split Recharts (charts library) into its own chunk - it's large
          'charts': ['recharts'],
          // Split Lucide icons into its own chunk
          'icons': ['lucide-react'],
          // Split date utilities into their own chunk
          'date-utils': ['date-fns'],
        },
      },
    },
    // Increase chunk size warning limit to 1000 kB
    chunkSizeWarningLimit: 1000,
  },
})
