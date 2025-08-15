import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173, // 可以自定义端口
    watch: {
      usePolling: true
    }
  },
  define: {
    global: 'window' // 将 `global` 映射到 `window`
  }
})
