from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class CompanyStatusUpdate(BaseModel):
    status: str


class ScrapingStatus(BaseModel):
    is_scraping: bool


class QualificationScore(BaseModel):
    financialStability: int
    equipmentNeed: int
    timing: int
    decisionAuthority: int


class CompanyResponse(BaseModel):
    id: int
    company: str  # discovered_name
    industry: str  # primary_industry
    location: str  # formatted location
    score: int  # calculated from qualification_score
    status: str
    lastActivity: str  # formatted updated_at
    createdAt: str  # formatted created_at
    equipmentNeed: str
    employees: Optional[str] = None  # employee_count
    website: str  # website_url or source_url
    sourceUrl: str
    email: Optional[str] = None  # contact_email
    phone: Optional[str] = None  # contact_phone
    notes: str  # initial_reasoning
    recentNews: Optional[str] = None  # recent_news
    qualificationScore: QualificationScore
    icpName: Optional[str] = None
    qualificationReasoning: Optional[str] = None
    estimatedRevenue: Optional[str] = None  # estimated_revenue
    description: Optional[str] = None  # enriched_data description

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int
    page: int
    limit: int


class DashboardStats(BaseModel):
    totalLeads: int
    qualifiedLeads: int
    inReviewLeads: int
    discoveredLeads: int
    qualificationRate: float
    avgScore: float
    topIndustries: List[dict]
