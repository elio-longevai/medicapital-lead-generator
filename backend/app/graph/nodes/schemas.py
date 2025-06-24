from typing import Optional
from pydantic import BaseModel, Field


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


class EnrichedCompanyData(BaseModel):
    """Vertegenwoordigt de gestructureerde gegevens geëxtraheerd van de website van een bedrijf."""

    contact_email: Optional[str] = Field(
        description="Primair contact e-mailadres of null", default=None
    )
    contact_phone: Optional[str] = Field(
        description="Primair telefoonnummer of null", default=None
    )
    location_details: Optional[str] = Field(
        description="Volledig adres/locatie of null", default=None
    )
    employee_count: Optional[str] = Field(
        description="Medewerkersaantal bereik (bijv. '10-50') of null", default=None
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
        description="Geschat jaaromzet bereik (bijv. '€1M-€5M') of null", default=None
    )
    qualification_details: QualificationDetails = Field(
        default_factory=QualificationDetails
    )
