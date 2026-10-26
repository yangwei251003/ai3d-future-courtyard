import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: "./",
  publicDir: '../assets/runtime',
  server: { port: 5173, strictPort: true },
  preview: { port: 4188, strictPort: true },
  build: { target: 'es2022' },
})
