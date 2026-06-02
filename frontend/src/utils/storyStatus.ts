import type { NodeStatus } from '@/types/models'

// 故事节点状态的中文展示标签（单一来源，避免各处散写英文枚举）
const STORY_STATUS_LABELS: Record<string, string> = {
  published: '已发布',
  pending: '待审核',
  archived: '已归档',
  ending: '已完结',
}

export function storyStatusLabel(status: NodeStatus | string | null | undefined): string {
  if (!status) return '未知'
  return STORY_STATUS_LABELS[status] ?? String(status)
}
