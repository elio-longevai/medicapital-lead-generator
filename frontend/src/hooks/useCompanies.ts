import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, type CompanyListResponse, type Company, type GetCompaniesParams, type ContactEnrichmentResponse } from '@/services/api';

export function useCompanies(params: GetCompaniesParams = {}) {
  return useQuery<CompanyListResponse>({
    queryKey: ['companies', params],
    queryFn: () => apiService.getCompanies(params),
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
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useUpdateCompanyStatus() {
  const queryClient = useQueryClient();
  return useMutation<Company, Error, { id: number; status: string }>({
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

export function useEnrichCompanyContacts() {
  const queryClient = useQueryClient();
  return useMutation<ContactEnrichmentResponse, Error, { id: number }>({
    mutationFn: ({ id }) => apiService.enrichCompanyContacts(id),
    onMutate: async ({ id }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['company', id] });

      // Snapshot the previous value
      const previousCompany = queryClient.getQueryData(['company', id]);

      // Optimistically update to show enrichment in progress
      queryClient.setQueryData(['company', id], (oldData: Company | undefined) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          contactEnrichmentStatus: 'pending' as const,
          contactEnrichmentProgress: 0,
          contactEnrichmentCurrentStep: 'Contactverrijking wordt gestart...',
        };
      });

      return { previousCompany };
    },
    onError: (err, variables, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousCompany) {
        queryClient.setQueryData(['company', variables.id], context.previousCompany);
      }
      
      // For 409 conflicts (concurrent enrichment), refresh data to get current state
      if (err.message.includes('409') || err.message.includes('already in progress')) {
        queryClient.invalidateQueries({ queryKey: ['company', variables.id] });
        queryClient.invalidateQueries({ queryKey: ['enrichment-status', variables.id] });
      }
    },
    onSettled: (data, error, variables) => {
      // Always refetch after mutation to get the latest data from server
      queryClient.invalidateQueries({ queryKey: ['company', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      
      // Also start polling for enrichment status if successful
      if (!error) {
        queryClient.invalidateQueries({ queryKey: ['enrichment-status', variables.id] });
      }
    },
  });
}
