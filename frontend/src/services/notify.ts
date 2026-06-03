import { createDiscreteApi } from 'naive-ui'
import { themeOverrides } from '@/theme'

// 拦截器在 Vue setup 之外，拿不到 useMessage()，用 discrete API。
// 与 App.vue 的 NConfigProvider 保持一致：不显式指定 theme，仅用 themeOverrides
// 在亮色基础上叠加，得到同一套黑白观感（避免 toast 与主界面的 token 基线分叉）。
const { message } = createDiscreteApi(['message'], {
  configProviderProps: {
    themeOverrides,
  },
})

// 限流提示去重窗口：狂点时同一条提示只在该时间内显示一次
const RATE_LIMIT_DEDUP_MS = 3000
let lastShownAt = 0

/** 429 限流提示：去重窗口内只弹一次，避免 toast 堆叠。 */
export function notifyRateLimited(detail?: string): void {
  const now = Date.now()
  if (now - lastShownAt < RATE_LIMIT_DEDUP_MS) return
  lastShownAt = now
  message.warning(detail || '操作过于频繁，请稍后再试')
}
