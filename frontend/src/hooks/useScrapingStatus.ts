import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';

export function useScrapingStatus() {
    return useQuery({
        queryKey: ['scraping-status'],
        queryFn: () => apiService.getScrapingStatus(),
        refetchInterval: (query) => (query.state.data?.is_scraping ? 5000 : false),
        refetchOnWindowFocus: true,
        staleTime: 0,
        gcTime: 0,
    });
}

export function useScrapeLeads() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: apiService.startScraping,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['scraping-status'] });
        },
    });
} 