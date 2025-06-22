from typing import Optional
from pydantic import BaseModel, Field


class QualificationDetails(BaseModel):
    """Represents the qualification scores for a lead."""

    financial_stability: int = Field(
        description="Score (0-100) based on company maturity, growth indicators, financial mentions",
        default=0,
    )
    equipment_need: int = Field(
        description="Score (0-100) based on explicit equipment needs, technology gaps, expansion plans",
        default=0,
    )
    timing: int = Field(
        description="Score (0-100) based on recent developments, expansion plans, immediate needs mentioned",
        default=0,
    )
    decision_authority: int = Field(
        description="Score (0-100) based on contact information quality, leadership visibility",
        default=0,
    )


class EnrichedCompanyData(BaseModel):
    """Represents the structured data extracted from a company's website."""

    contact_email: Optional[str] = Field(
        description="Primary contact email or null", default=None
    )
    contact_phone: Optional[str] = Field(
        description="Primary phone number or null", default=None
    )
    location_details: Optional[str] = Field(
        description="Full address/location or null", default=None
    )
    employee_count: Optional[str] = Field(
        description="Employee range (e.g., '10-50') or null", default=None
    )
    equipment_needs: Optional[str] = Field(
        description="Specific equipment/technology needs mentioned or null",
        default=None,
    )
    recent_news: Optional[str] = Field(
        description="Latest developments, news, or updates or null", default=None
    )
    website_url: Optional[str] = Field(
        description="Official website URL or null", default=None
    )
    enriched_data: Optional[str] = Field(
        description="Brief summary of key business information", default=None
    )
    qualification_details: QualificationDetails = Field(
        default_factory=QualificationDetails
    )
