// TODO: Make API_BASE_URL configurable via environment variables for different deployment environments
const API_BASE_URL = 'http://localhost:8000';

export interface Company {
  id: number;
  company: string;
  industry: string;
  location: string;
  score: number;
  status: string;
  lastActivity: string;
  equipmentNeed: string;
  estimatedValue: string;
  employees: string;
  website: string;
  email?: string;
  phone?: string;
  notes: string;
  recentNews?: string;
  qualificationScore: {
    financialStability: number;
    equipmentNeed: number;
    timing: number;
    decisionAuthority: number;
  };
}

export interface CompanyListResponse {
  companies: Company[];
  total: number;
  page: number;
  limit: number;
}

export interface DashboardStats {
  totalLeads: number;
  qualifiedLeads: number;
  inReviewLeads: number;
  discoveredLeads: number;
  qualificationRate: number;
  avgScore: number;
  topIndustries: Array<{industry: string; count: number}>;
}

class ApiService {
  async getCompanies(params: {
    skip?: number;
    limit?: number;
    industry?: string;
    status?: string;
    country?: string;
    search?: string;
    sort_by?: string;
  } = {}): Promise<CompanyListResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });
    
    const response = await fetch(`${API_BASE_URL}/api/companies?${searchParams}`);
    if (!response.ok) throw new Error('Failed to fetch companies');
    return response.json();
  }

  async getCompany(id: number): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/api/companies/${id}`);
    if (!response.ok) throw new Error('Failed to fetch company');
    return response.json();
  }

  async updateCompanyStatus(id: number, status: 'contacted' | 'rejected'): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/api/companies/${id}/status`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to update company status to ${status}`);
    }
    return response.json();
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
    if (!response.ok) throw new Error('Failed to fetch dashboard stats');
    return response.json();
  }
}

export const apiService = new ApiService();
