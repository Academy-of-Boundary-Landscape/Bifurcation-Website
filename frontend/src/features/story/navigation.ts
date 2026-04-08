import type { RouteLocationRaw } from 'vue-router'

export function buildStoryWriteRoute(bookId: number, parentId?: number | null): RouteLocationRaw {
  return {
    name: 'story-write',
    params: { bookId },
    query: parentId ? { parentId } : {},
  }
}
