const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  // Add https:// if the URL doesn't have a protocol
  if (envUrl && !envUrl.startsWith('http://') && !envUrl.startsWith('https://')) {
    return `https://${envUrl}`;
  }
  return envUrl;
};

const API_BASE_URL = getApiBaseUrl();

export interface Contact {
  name?: string;
  role?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  department?: string;
  seniority_level?: string;
}

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
  entityType?: 'end_user' | 'supplier' | 'other';
  subIndustry?: string;
  contactPersons?: Contact[];
  contactEnrichmentStatus?: 'not_started' | 'pending' | 'completed' | 'failed';
  contactEnrichedAt?: string;
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

export interface GetCompaniesParams {
  skip?: number;
  icp_name?: string;
  status?: string;
  country?: string;
  search?: string;
  entity_type?: string;
  sub_industry?: string;
  sort_by?: string;
}

export interface ScrapingStatus {
  is_scraping: boolean;
}

export interface ContactEnrichmentResponse {
  message: string;
  companyId: string;
}

export interface EnrichmentStatusResponse {
  companyId: string;
  companyName: string;
  status: 'not_started' | 'pending' | 'completed' | 'failed';
  progress: number; // 0-100
  currentStep?: string;
  stepsCompleted: Array<{
    step: string;
    description: string;
    completed_at: string;
  }>;
  errorDetails?: {
    error: string;
    details: string;
    step: string;
  };
  retryCount: number;
  startedAt?: string;
  completedAt?: string;
  contactsFound: number;
  lastUpdated?: string;
}

class ApiService {
  async getCompanies(params: GetCompaniesParams = {}): Promise<CompanyListResponse> {
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

  async enrichCompanyContacts(companyId: number): Promise<ContactEnrichmentResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companies/${companyId}/enrich-contacts`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Onbekende fout bij het verrijken van contacten.",
      }));
      throw new Error(
        errorData.detail || `Contactverrijking mislukt: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async getEnrichmentStatus(companyId: number): Promise<EnrichmentStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/companies/${companyId}/enrichment-status`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Kon verrijkingsstatus niet ophalen.",
      }));
      throw new Error(
        errorData.detail || `Status ophalen mislukt: ${response.statusText}`,
      );
    }
    return response.json();
  }
}

export const apiService = new ApiService();
