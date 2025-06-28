const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface Company {
  id: number;
  company: string;
  industry: string;
  location: string;
  score: number;
  status: string;
  lastActivity: string;
  createdAt: string;
  equipmentNeed: string;
  employees: string;
  website: string;
  sourceUrl: string;
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
  icpName?: string;
  qualificationReasoning?: string;
  estimatedRevenue?: string;
  description?: string;
}

export interface CompanyListResponse {
  companies: Company[];
  total: number;
}

export interface DashboardStats {
  totalLeads: number;
  qualifiedLeads: number;
  inReviewLeads: number;
  discoveredLeads: number;
  leadsThisWeek: number;
  qualificationRate: number;
  avgScore: number;
  topIndustries: Array<{ industry: string; count: number }>;
}

export interface ScrapingStatus {
  is_scraping: boolean;
}

class ApiService {
  async getCompanies(params: {
    skip?: number;
    icp_name?: string;
    status?: string;
    country?: string;
    search?: string;
    sort_by?: string;
  } = {}): Promise<CompanyListResponse> {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    }

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

  async getScrapingStatus(): Promise<ScrapingStatus> {
    const response = await fetch(`${API_BASE_URL}/api/scrape-status`);
    if (!response.ok) throw new Error('Failed to fetch scraping status');
    return response.json();
  }

  async startScraping(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/scrape-leads`, {
      method: "POST",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Onbekende serverfout, controleer de backend logs.",
      }));
      throw new Error(
        errorData.detail || `Serverfout: ${response.statusText}`,
      );
    }
    return response.json();
  }
}

export const apiService = new ApiService();
