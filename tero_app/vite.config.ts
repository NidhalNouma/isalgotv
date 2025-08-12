import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: "/static/",
  build: {
    outDir: '_out',
    manifest: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'src/main.tsx'),
    },
  },
  server: {
    // allow Vite’s dev server to serve JS to your Django origin:
    cors: {
      origin: ['http://tero.myproject.local:8000'],
      // you can also allow all origins in dev with `cors: true`
      // (but that’s less secure – be explicit if you can)
    },
    // if you need HMR to connect back to your custom hostname:
    hmr: {
      host: 'tero.myproject.local',
      protocol: 'ws',
      // clientPort: 5173, // only if your setup needs an explicit port
    },
    // (optional) ensure Vite listens on all interfaces so your custom host
    // actually reaches it:
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
  }
})