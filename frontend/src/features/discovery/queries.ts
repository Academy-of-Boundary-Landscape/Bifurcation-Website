import { useQuery } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { fetchFeaturedNodes, fetchLatestFeed, fetchTrendingNodes, searchDiscoveryNodes } from './api'
import { queryKeys } from '@/features/queryKeys'

export function useFeaturedNodesQuery(params?: { limit?: number }) {
  return useQuery({
    queryKey: queryKeys.featuredNodes(params),
    queryFn: () => fetchFeaturedNodes(params),
  })
}

export function useLatestFeedQuery(params?: { bookId?: number; skip?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.latestFeed(params),
    queryFn: () => fetchLatestFeed(params),
  })
}

export function useTrendingNodesQuery(params?: { days?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.trendingNodes(params),
    queryFn: () => fetchTrendingNodes(params),
  })
}

export function useDiscoverySearchQuery(keyword: MaybeRefOrGetter<string>, params?: { limit?: number }) {
  return useQuery({
    queryKey: computed(() => queryKeys.discoverySearch(toValue(keyword), params)),
    queryFn: () => searchDiscoveryNodes({ q: toValue(keyword).trim(), limit: params?.limit }),
    enabled: computed(() => toValue(keyword).trim().length > 0),
  })
}
