import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from ..db.models import Company
from ..api.models import (
    CompanyResponse,
    CompanyListResponse,
    DashboardStats,
    QualificationScore,
)
from typing import Optional

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    def get_companies_with_filters(
        self,
        skip: int,
        limit: int,
        icp_name: Optional[str],
        status: Optional[str],
        country: Optional[str],
        search: Optional[str],
        sort_by: str,
    ) -> CompanyListResponse:
        query = self.db.query(Company)

        # Apply filters
        if icp_name and icp_name != "all":
            query = query.filter(Company.icp_name == icp_name)
        if status and status != "all":
            query = query.filter(Company.status == status)
        elif not status or status == "all":
            # By default, do not show rejected leads
            query = query.filter(Company.status != "rejected")
        if country:
            query = query.filter(Company.country == country)
        if search:
            query = query.filter(
                Company.discovered_name.ilike(f"%{search}%")
                | Company.equipment_needs.ilike(f"%{search}%")
            )

        # Apply sorting
        if sort_by == "score":
            query = query.order_by(desc(Company.qualification_score))
        elif sort_by == "company":
            query = query.order_by(asc(Company.discovered_name))
        elif sort_by == "activity":
            query = query.order_by(desc(Company.created_at))

        total = query.count()
        companies = query.offset(skip).limit(limit).all()

        return CompanyListResponse(
            companies=[self._transform_company(c) for c in companies],
            total=total,
            page=skip // limit + 1,
            limit=limit,
        )

    def get_company_by_id(self, company_id: int) -> Optional[CompanyResponse]:
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        return self._transform_company(company)

    def update_company_status(
        self, company_id: int, new_status: str
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

        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None

        company.status = new_status
        # updated_at is handled by SQLAlchemy's onupdate trigger, so no manual setting needed.
        self.db.commit()
        self.db.refresh(company)
        return self._transform_company(company)

    def get_dashboard_statistics(self) -> DashboardStats:
        total_leads = self.db.query(Company).count()
        qualified_leads = (
            self.db.query(Company).filter(Company.status == "qualified").count()
        )
        in_review_leads = (
            self.db.query(Company).filter(Company.status == "in_review").count()
        )
        discovered_leads = (
            self.db.query(Company).filter(Company.status == "discovered").count()
        )

        qualification_rate = (
            (qualified_leads / total_leads * 100) if total_leads > 0 else 0
        )

        # Calculate average score
        avg_score_result = self.db.query(func.avg(Company.qualification_score)).scalar()
        avg_score = float(avg_score_result) if avg_score_result else 75.0

        # Get top ICPs
        top_icps = (
            self.db.query(Company.icp_name, func.count(Company.id).label("count"))
            .filter(Company.icp_name.isnot(None))
            .group_by(Company.icp_name)
            .order_by(desc("count"))
            .limit(3)
            .all()
        )

        return DashboardStats(
            totalLeads=total_leads,
            qualifiedLeads=qualified_leads,
            inReviewLeads=in_review_leads,
            discoveredLeads=discovered_leads,
            qualificationRate=qualification_rate,
            avgScore=avg_score,
            topIndustries=[
                {"industry": icp_name, "count": count} for icp_name, count in top_icps
            ],
        )

    def _transform_company(self, company: Company) -> CompanyResponse:
        # Calculate overall score
        score = company.qualification_score or self._calculate_default_score(company)

        # Parse qualification details safely
        qual_details = company.qualification_details or {}
        qualification_score = QualificationScore(
            financialStability=qual_details.get("financial_stability", 75),
            equipmentNeed=qual_details.get("equipment_need", 80),
            timing=qual_details.get("timing", 70),
            decisionAuthority=qual_details.get("decision_authority", 75),
        )

        # Format location
        location = f"{company.location_details or 'Onbekend'}, {company.country}"

        # Format last activity
        last_activity = (
            company.updated_at.strftime("%b %d, %Y")
            if company.updated_at
            else "Onbekend"
        )
        created_at = (
            company.created_at.strftime("%b %d, %Y")
            if company.created_at
            else "Onbekend"
        )

        # Use company_description field directly
        description = company.company_description

        return CompanyResponse(
            id=company.id,
            company=company.discovered_name,
            industry=company.primary_industry or "Onbekend",
            location=location,
            score=score,
            status=company.status,
            lastActivity=last_activity,
            createdAt=created_at,
            equipmentNeed=company.equipment_needs
            or self._infer_equipment_need(company),
            employees=company.employee_count,
            website=company.website_url or company.source_url,
            sourceUrl=company.source_url,
            email=company.contact_email,
            phone=company.contact_phone,
            notes=company.initial_reasoning,
            recentNews=company.recent_news,
            qualificationScore=qualification_score,
            icpName=company.icp_name,
            qualificationReasoning=company.qualification_reasoning,
            estimatedRevenue=company.estimated_revenue,
            description=description,
        )

    def _calculate_default_score(self, company: Company) -> int:
        # Base score calculation logic
        base_score = 70
        if company.primary_industry in ["Gezondheidszorg", "Medisch"]:
            base_score += 15
        elif company.primary_industry in ["Beauty & Wellness", "Wellness"]:
            base_score += 10
        return min(base_score, 95)

    def _infer_equipment_need(self, company: Company) -> str:
        industry_equipment = {
            "Gezondheidszorg": "Medische apparatuur",
            "Duurzaamheid": "Duurzame technologie",
            "Beauty & Wellness": "Beauty-apparatuur",
            "Horeca": "Keukenapparatuur",
        }
        return industry_equipment.get(company.primary_industry, "Apparatuur")
