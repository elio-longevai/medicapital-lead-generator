import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..api.models import (
    CompanyListResponse,
    CompanyResponse,
    DashboardStats,
    QualificationScore,
)
from ..db.repositories import CompanyRepository

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self):
        self.repo = CompanyRepository()

    def get_companies_with_filters(
        self,
        skip: int,
        icp_name: Optional[str],
        status: Optional[str],
        country: Optional[str],
        search: Optional[str],
        entity_type: Optional[str],
        sub_industry: Optional[str],
        sort_by: str,
    ) -> CompanyListResponse:
        # Handle grouped ICP business logic at the service layer
        if icp_name == "duurzaamheid":
            # Use the optimized repository method with multiple ICP names
            icp_names = ["sustainability_supplier", "sustainability_end_user"]
            result = self.repo.find_with_filters(
                skip=skip,
                icp_name=icp_names,
                status=status,
                country=country,
                search=search,
                entity_type=entity_type,
                sub_industry=sub_industry,
                sort_by=sort_by,
            )

            return CompanyListResponse(
                companies=[self._transform_company(c) for c in result["companies"]],
                total=result["total"],
            )
        else:
            # For all other cases, use the standard repository method
            result = self.repo.find_with_filters(
                skip=skip,
                icp_name=icp_name,
                status=status,
                country=country,
                search=search,
                entity_type=entity_type,
                sub_industry=sub_industry,
                sort_by=sort_by,
            )

            return CompanyListResponse(
                companies=[self._transform_company(c) for c in result["companies"]],
                total=result["total"],
            )

    def get_company_by_id(self, company_id: str) -> Optional[CompanyResponse]:
        company = self.repo.find_by_id(company_id)
        if not company:
            return None
        return self._transform_company(company)

    def update_company_status(
        self, company_id: str, new_status: str
    ) -> Optional[CompanyResponse]:
        """Updates the status of a single company and returns the transformed response."""
        valid_statuses = [
            "discovered",
            "in_review",
            "qualified",
            "contacted",
            "rejected",
        ]
        if new_status not in valid_statuses:
            return None  # Invalid status, handled in API layer

        # Update the status
        success = self.repo.update_status(company_id, new_status)
        if not success:
            return None

        # Return the updated company
        company = self.repo.find_by_id(company_id)
        if not company:
            return None

        return self._transform_company(company)

    def get_dashboard_statistics(self) -> DashboardStats:
        stats = self.repo.get_statistics()

        total_leads = stats["total_leads"]
        qualified_leads = stats["qualified_leads"]
        in_review_leads = stats["in_review_leads"]
        discovered_leads = stats["discovered_leads"]
        leads_this_week = stats["leads_this_week"]

        qualification_rate = (
            (qualified_leads / total_leads * 100) if total_leads > 0 else 0
        )

        return DashboardStats(
            totalLeads=total_leads,
            qualifiedLeads=qualified_leads,
            inReviewLeads=in_review_leads,
            discoveredLeads=discovered_leads,
            leadsThisWeek=leads_this_week,
            qualificationRate=qualification_rate,
            avgScore=stats["avg_score"],
            topIndustries=[
                {"industry": item["_id"], "count": item["count"]}
                for item in stats["top_icps"]
            ],
        )

    def _transform_company(self, company: Dict[str, Any]) -> CompanyResponse:
        # Calculate overall score
        score = company.get("qualification_score") or self._calculate_default_score(
            company
        )

        # Parse qualification details safely
        qual_details = company.get("qualification_details") or {}
        qualification_score = QualificationScore(
            financialStability=qual_details.get("financial_stability", 75),
            equipmentNeed=qual_details.get("equipment_need", 80),
            timing=qual_details.get("timing", 70),
            decisionAuthority=qual_details.get("decision_authority", 75),
        )

        # Format location
        location = f"{company.get('location_details') or 'Onbekend'}, {company.get('country', '')}"

        # Format last activity - return full ISO datetime instead of date-only
        from datetime import timezone

        updated_at = company.get("updated_at")
        last_activity = (
            updated_at.replace(tzinfo=timezone.utc).isoformat()
            if updated_at and isinstance(updated_at, datetime)
            else None
        )

        created_at = company.get("created_at")
        created_at_formatted = (
            created_at.replace(tzinfo=timezone.utc).isoformat()
            if created_at and isinstance(created_at, datetime)
            else None
        )

        # Use company_description field directly
        description = company.get("company_description")

        # Get first available email/phone from contact_persons list for summary display
        contact_persons = company.get("contact_persons", [])
        primary_email = None
        primary_phone = None

        # Find first contact with email
        for contact in contact_persons:
            if contact.get("email") and not primary_email:
                primary_email = contact.get("email")

        # Find first contact with phone
        for contact in contact_persons:
            if contact.get("phone") and not primary_phone:
                primary_phone = contact.get("phone")

        return CompanyResponse(
            id=str(company["_id"]),  # Convert ObjectId to string
            company=company.get("discovered_name", ""),
            industry=company.get("primary_industry") or "Onbekend",
            location=location,
            score=score,
            status=company.get("status", "discovered"),
            lastActivity=last_activity,
            createdAt=created_at_formatted,
            equipmentNeed=company.get("equipment_needs")
            or self._infer_equipment_need(company),
            employees=company.get("employee_count") or "Niet gevonden",
            website=company.get("website_url") or company.get("source_url", ""),
            sourceUrl=company.get("source_url", ""),
            email=primary_email,
            phone=primary_phone,
            notes=company.get("initial_reasoning", ""),
            recentNews=company.get("recent_news"),
            qualificationScore=qualification_score,
            icpName=company.get("icp_name"),
            qualificationReasoning=company.get("qualification_reasoning"),
            estimatedRevenue=company.get("estimated_revenue"),
            description=description,
            entityType=company.get("entity_type"),
            subIndustry=company.get("sub_industry"),
            contactPersons=company.get("contact_persons", []),
            contactEnrichmentStatus=company.get("contact_enrichment_status"),
            contactEnrichedAt=(
                company.get("contact_enriched_at")
                .replace(tzinfo=timezone.utc)
                .isoformat()
                if company.get("contact_enriched_at")
                and isinstance(company.get("contact_enriched_at"), datetime)
                else None
            ),
            # Enhanced enrichment progress fields
            contactEnrichmentProgress=company.get("contact_enrichment_progress"),
            contactEnrichmentCurrentStep=company.get("contact_enrichment_current_step"),
            contactEnrichmentStepsCompleted=company.get(
                "contact_enrichment_steps_completed", []
            ),
            contactEnrichmentErrorDetails=company.get(
                "contact_enrichment_error_details"
            ),
            contactEnrichmentRetryCount=company.get("contact_enrichment_retry_count"),
            contactEnrichmentStartedAt=(
                company.get("contact_enrichment_started_at")
                .replace(tzinfo=timezone.utc)
                .isoformat()
                if company.get("contact_enrichment_started_at")
                and isinstance(company.get("contact_enrichment_started_at"), datetime)
                else None
            ),
            contactEnrichmentLastUpdated=company.get("contact_enrichment_last_updated"),
        )

    def _calculate_default_score(self, company: Dict[str, Any]) -> int:
        # Base score calculation logic
        base_score = 70
        primary_industry = company.get("primary_industry", "")
        if primary_industry in ["Gezondheidszorg", "Medisch"]:
            base_score += 15
        elif primary_industry in ["Beauty & Wellness", "Wellness"]:
            base_score += 10
        return min(base_score, 95)

    def _infer_equipment_need(self, company: Dict[str, Any]) -> str:
        industry_equipment = {
            "Gezondheidszorg": "Medische apparatuur",
            "Duurzaamheid": "Duurzame technologie",
            "Beauty & Wellness": "Beauty-apparatuur",
            "Horeca": "Keukenapparatuur",
        }
        primary_industry = company.get("primary_industry", "")
        return industry_equipment.get(primary_industry, "Apparatuur")
