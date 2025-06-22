import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, type CompanyListResponse, type Company } from '@/services/api';

export function useCompanies(params: {
  skip?: number;
  limit?: number;
  icp_name?: string;
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

export function useUpdateCompanyStatus() {
  const queryClient = useQueryClient();
  return useMutation<Company, Error, { id: number; status: 'contacted' | 'rejected' }>({
    mutationFn: ({ id, status }) => apiService.updateCompanyStatus(id, status),
    onSuccess: (data, variables) => {
      // Invalidate queries to refetch data from the server
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });

      // Also update the specific company's data in the cache if it exists
      queryClient.setQueryData(['company', variables.id], data);
    },
  });
}
