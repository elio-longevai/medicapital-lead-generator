import { useQuery } from '@tanstack/react-query';
import { apiService, type CompanyListResponse } from '@/services/api';

export function useCompanies(params: {
  skip?: number;
  limit?: number;
  industry?: string;
  status?: string;
  search?: string;
  sort_by?: string;
} = {}) {
  return useQuery<CompanyListResponse>({
    queryKey: ['companies', params],
    queryFn: () => apiService.getCompanies(params),
    // TODO: Make cache time configurable via app settings
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCompany(id: number) {
  return useQuery({
    queryKey: ['company', id],
    queryFn: () => apiService.getCompany(id),
    enabled: !!id,
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiService.getDashboardStats(),
    // TODO: Make cache time configurable via app settings
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
