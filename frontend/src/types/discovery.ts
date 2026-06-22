import type { RouteLocationRaw } from 'vue-router'

export type DiscoveryRailStatus = 'published' | 'pending' | 'archived' | 'neutral'

export interface DiscoveryRailAction {
  label: string
  to: string | RouteLocationRaw
}

export interface DiscoveryRailMetric {
  label: string
  value: string
}

export interface DiscoveryRailItem {
  id: string | number
  title: string
  summary: string
  badge: string
  badgeTone?: 'default' | 'strong'
  meta: string[]
  metrics?: DiscoveryRailMetric[]
  hint?: string
  action: DiscoveryRailAction
  /** 次级动作（如登录用户的"续写"快捷入口）；不影响 `action` 主按钮 */
  secondaryAction?: DiscoveryRailAction
  status?: DiscoveryRailStatus
}

export interface DiscoveryRailProps {
  kicker: string
  title: string
  description?: string
  items?: DiscoveryRailItem[]
  loading?: boolean
  error?: Error | null
  emptyText?: string
  actionLabel?: string
  actionTo?: string
}
