import type { StoryNode } from '@/types/models'

export type DiscoveryRailStatus = 'published' | 'pending' | 'archived' | 'neutral'

export interface DiscoveryRailAction {
  label: string
  to: string
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
  status?: DiscoveryRailStatus
}

export interface DiscoveryRailProps {
  kicker: string
  title: string
  description: string
  items?: DiscoveryRailItem[]
  loading?: boolean
  error?: Error | null
  emptyText?: string
  actionLabel?: string
  actionTo?: string
}

export interface DiscoveryNodeRecommendationSource {
  nodes: StoryNode[]
}

export interface DiscoverySectionResponse<TItem = StoryNode> {
  section_key: string
  title: string
  description?: string | null
  algorithm_key?: string | null
  items: TItem[]
}
