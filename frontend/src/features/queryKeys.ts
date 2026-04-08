export const queryKeys = {
  books: (params?: { phase?: string }) => ['books', params] as const,
  booksRoot: () => ['books'] as const,
  book: (bookId: number) => ['book', bookId] as const,
  featuredNodes: (params?: { limit?: number }) => ['featured-nodes', params] as const,
  latestFeed: (params?: { bookId?: number; skip?: number; limit?: number }) => ['latest-feed', params] as const,
  trendingNodes: (params?: { days?: number; limit?: number }) => ['trending-nodes', params] as const,
  discoverySearch: (keyword: string, params?: { limit?: number }) => ['discovery-search', keyword, params] as const,
  storyTreesRoot: () => ['story-tree'] as const,
  storyTree: (bookId: number) => ['story-tree', bookId] as const,
  storyNode: (nodeId: number) => ['story-node', nodeId] as const,
  storyLineage: (nodeId: number) => ['story-lineage', nodeId] as const,
  nodePath: (nodeId: number) => ['node-path', nodeId] as const,
  nodeChildren: (nodeId: number) => ['node-children', nodeId] as const,
  nodeCommentsRoot: () => ['node-comments'] as const,
  nodeComments: (nodeId: number, params?: { skip?: number; limit?: number }) => ['node-comments', nodeId, params] as const,
  pendingNodes: (params?: { skip?: number; limit?: number }) => ['pending-nodes', params] as const,
  pendingNodesRoot: () => ['pending-nodes'] as const,
  adminNodes: (params?: {
    skip?: number
    limit?: number
    status?: string
    book_id?: number
    author_id?: number
    keyword?: string
  }) => ['admin-nodes', params] as const,
  adminNodesRoot: () => ['admin-nodes'] as const,
  adminStats: () => ['admin-stats'] as const,
  adminUsers: (params?: { skip?: number; limit?: number; role?: string; is_active?: boolean; keyword?: string }) => ['admin-users', params] as const,
  adminUsersRoot: () => ['admin-users'] as const,
  userProfile: () => ['user-profile'] as const,
  userNodes: (params?: { authorId?: number; limit?: number }) => ['user-nodes', params] as const,
  notificationsRoot: () => ['notifications'] as const,
  notifications: (params?: { skip?: number; limit?: number }) => ['notifications', params] as const,
  unreadCount: () => ['unread-count'] as const,
}
