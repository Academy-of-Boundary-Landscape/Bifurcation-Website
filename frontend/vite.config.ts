import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import UnoCSS from 'unocss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devServerPort = Number(env.VITE_PORT || '5173')
  const inferredApiProxyTarget = devServerPort === 5174 ? 'http://127.0.0.1:8401' : 'http://localhost:8057'
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || inferredApiProxyTarget

  return {
    plugins: [
      vue(),
      vueDevTools(),
      UnoCSS(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    server: {
      port: Number.isFinite(devServerPort) ? devServerPort : 5173,
      proxy: {
        '/api/v1': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
