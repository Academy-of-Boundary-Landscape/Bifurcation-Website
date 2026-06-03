import { createDiscreteApi, darkTheme } from 'naive-ui'
import { themeOverrides } from '@/theme'

// 拦截器在 Vue setup 之外，拿不到 useMessage()，用 discrete API。
// 复用暗色主题保持黑白风格一致。
const { message } = createDiscreteApi(['message'], {
  configProviderProps: {
    theme: darkTheme,
    themeOverrides,
  },
})

let lastShownAt = 0

/** 429 限流提示：3 秒内去重，避免狂点时 toast 堆叠。 */
export function notifyRateLimited(detail?: string): void {
  const now = Date.now()
  if (now - lastShownAt < 3000) return
  lastShownAt = now
  message.warning(detail || '操作过于频繁，请稍后再试')
}
