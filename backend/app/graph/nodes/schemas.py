import logging
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


class QualificationDetails(BaseModel):
    """Vertegenwoordigt de kwalificatiescores voor een lead."""

    financial_stability: int = Field(
        description="Score (0-100) gebaseerd op bedrijfsvolwassenheid, groei-indicatoren, financiële vermeldingen",
        default=0,
    )
    equipment_need: int = Field(
        description="Score (0-100) gebaseerd op expliciete apparatuurbehoeften, technologische tekortkomingen, uitbreidingsplannen",
        default=0,
    )
    timing: int = Field(
        description="Score (0-100) gebaseerd op recente ontwikkelingen, uitbreidingsplannen, genoemde onmiddellijke behoeften",
        default=0,
    )
    decision_authority: int = Field(
        description="Score (0-100) gebaseerd op de kwaliteit van contactinformatie, zichtbaarheid van leiderschap",
        default=0,
    )


class ContactPerson(BaseModel):
    """Represents a single contact person extracted from a website."""

    name: Optional[str] = Field(
        description="Full name of the contact person", default=None
    )
    role: Optional[str] = Field(
        description="Job title or role of the contact", default=None
    )
    email: Optional[str] = Field(
        description="Email address of the contact", default=None
    )
    phone: Optional[str] = Field(
        description="Phone number of the contact", default=None
    )
    linkedin_url: Optional[str] = Field(
        description="LinkedIn profile URL", default=None
    )
    department: Optional[str] = Field(
        description="Department (HR, Finance, Operations, Sales, etc.)", default=None
    )
    seniority_level: Optional[str] = Field(
        description="Seniority level (C-Level, Director, Manager, etc.)", default=None
    )


class EnrichedCompanyData(BaseModel):
    """Vertegenwoordigt de gestructureerde gegevens geëxtraheerd van de website van een bedrijf."""

    entity_type: Literal["end_user", "supplier", "other"] = Field(
        description="Type of company: 'end_user', 'supplier', or 'other'",
        default="other",
    )

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v):
        """Ensure entity_type is one of the three allowed values."""
        allowed_values = {"end_user", "supplier", "other"}
        if v not in allowed_values:
            # Log the invalid value for debugging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid entity_type '{v}' received, defaulting to 'other'")
            return "other"
        return v

    sub_industry: Optional[str] = Field(
        description="Specific sub-industry classification in Dutch", default=None
    )
    contacts: Optional[List[ContactPerson]] = Field(
        description="List of key contact persons", default_factory=list
    )
    location_details: Optional[str] = Field(
        description="Volledig adres/locatie of null", default=None
    )
    employee_count: Optional[str] = Field(
        description="Medewerkersaantal (employee count) (bijv. '10-50') of null",
        default=None,
    )
    equipment_needs: Optional[str] = Field(
        description="Specifieke genoemde apparatuur/technologiebehoeften of null",
        default=None,
    )
    recent_news: Optional[str] = Field(
        description="Laatste ontwikkelingen, nieuws of updates of null", default=None
    )
    website_url: Optional[str] = Field(
        description="Officiële website URL of null", default=None
    )
    company_description: Optional[str] = Field(
        description="Korte, feitelijke samenvatting van de kernactiviteiten, missie en waardepropositie van het bedrijf in het Nederlands.",
        default=None,
    )
    estimated_revenue: Optional[str] = Field(
        description="Geschatte jaaromzet (annual revenue) (bijv. '€1M-€5M') of null",
        default=None,
    )
    qualification_details: QualificationDetails = Field(
        default_factory=QualificationDetails
    )
