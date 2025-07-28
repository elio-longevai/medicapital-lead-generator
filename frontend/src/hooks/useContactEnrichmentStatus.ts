import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { apiService, type EnrichmentStatusResponse } from '@/services/api';

export function useContactEnrichmentStatus(companyId: number) {
  const queryClient = useQueryClient();

  const query = useQuery<EnrichmentStatusResponse>({
    queryKey: ['enrichment-status', companyId],
    queryFn: () => apiService.getEnrichmentStatus(companyId),
    enabled: !!companyId,
    staleTime: 0, // Always consider data stale to ensure fresh polling
    gcTime: 0, // Don't cache old data
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll every 2 seconds if enrichment is pending, otherwise stop polling
      return data?.status === 'pending' ? 2000 : false;
    },
    refetchOnWindowFocus: true,
    refetchOnMount: true,
  });

  // Handle side effects when enrichment completes
  useEffect(() => {
    if (query.data && (query.data.status === 'completed' || query.data.status === 'failed')) {
      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['company', companyId] });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    }
  }, [query.data, companyId, queryClient]);

  return query;
}

export function useContactEnrichmentPolling(companyId: number, isEnriching: boolean) {
  /**
   * Alternative hook for more granular control over polling.
   * Use this when you want to start/stop polling based on external conditions.
   */
  return useQuery<EnrichmentStatusResponse>({
    queryKey: ['enrichment-status', companyId],
    queryFn: () => apiService.getEnrichmentStatus(companyId),
    enabled: !!companyId && isEnriching,
    staleTime: 0,
    gcTime: 0,
    refetchInterval: isEnriching ? 2000 : false,
    refetchOnWindowFocus: false, // Don't refetch on window focus for this variant
    refetchOnMount: true,
  });
}