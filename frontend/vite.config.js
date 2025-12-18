import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

<<<<<<< HEAD
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
=======
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
>>>>>>> 97953c3 (Initial commit from Specify template)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
<<<<<<< HEAD
=======
        rewrite: (path) => path.replace(/^\/api/, ''),
>>>>>>> 97953c3 (Initial commit from Specify template)
      },
    },
  },
})
<<<<<<< HEAD

=======
>>>>>>> 97953c3 (Initial commit from Specify template)
