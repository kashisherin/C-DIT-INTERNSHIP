import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // This allows ngrok to connect properly
    allowedHosts: ['living-stylized-crawling.ngrok-free.dev'] // Add your specific ngrok URL here
  }
})