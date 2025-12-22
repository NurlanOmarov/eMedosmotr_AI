import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: false,
    hmr: {
      clientPort: 5173
    },
    // Allow all hosts for Docker/proxy access
    allowedHosts: [
      '.iproject.sbs',
      'iproject.sbs',
      'www.iproject.sbs',
      'emedosmotr_frontend',
      '172.19.0.4',
      '69.197.178.118'
    ]
  }
})
