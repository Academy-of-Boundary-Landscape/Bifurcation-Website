import type { StoryNode, StoryNodeRead, StoryNodeTreeItem } from '@/types/models'

type CreatableNodeLike = Pick<StoryNode, 'status' | 'is_ending' | 'freeze_interactions'>

export function canCreateFromStoryNode(node: CreatableNodeLike | null | undefined) {
  if (!node) {
    return false
  }

  return node.status === 'published' && !node.is_ending && !node.freeze_interactions
}

export function getStoryNodeCreationBlockedReason(node: CreatableNodeLike | null | undefined) {
  if (!node) {
    return ''
  }

  if (node.freeze_interactions) {
    return '该节点已冻结互动，暂不可继续创作后续节点。'
  }

  if (node.is_ending) {
    return '该分支已经完结，不能再继续扩展。'
  }

  if (node.status === 'pending') {
    return '该节点正在审核中，审核通过后才能继续续写。'
  }

  if (node.status === 'archived') {
    return '该节点已归档，不能继续作为公开分支起点。'
  }

  return ''
}

export type StoryCreatableNode = StoryNode | StoryNodeRead | StoryNodeTreeItem
