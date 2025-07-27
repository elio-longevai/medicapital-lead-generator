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


class ContactPersonResponse(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    department: Optional[str] = None
    seniority_level: Optional[str] = None


class CompanyResponse(BaseModel):
    id: str  # MongoDB ObjectId as string
    company: str  # discovered_name
    industry: str  # primary_industry
    location: str  # formatted location
    score: int  # calculated from qualification_score
    status: str
    lastActivity: Optional[str] = (
        None  # formatted updated_at - now ISO datetime or None
    )
    createdAt: Optional[str] = None  # formatted created_at - now ISO datetime or None
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
    entityType: Optional[str] = None  # entity_type
    subIndustry: Optional[str] = None  # sub_industry
    contactPersons: Optional[List[ContactPersonResponse]] = (
        None  # contact_persons (enriched)
    )
    contactEnrichmentStatus: Optional[str] = None  # contact_enrichment_status
    contactEnrichedAt: Optional[str] = None  # contact_enriched_at

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int


class DashboardStats(BaseModel):
    totalLeads: int
    qualifiedLeads: int
    inReviewLeads: int
    discoveredLeads: int
    leadsThisWeek: int
    qualificationRate: float
    avgScore: float
    topIndustries: List[dict]
