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


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    def get_companies_with_filters(
        self,
        skip: int,
        limit: int,
        industry: Optional[str],
        status: Optional[str],
        country: Optional[str],
        search: Optional[str],
        sort_by: str,
    ) -> CompanyListResponse:
        query = self.db.query(Company)

        # Apply filters
        if industry and industry != "all":
            query = query.filter(Company.primary_industry == industry)
        if status and status != "all":
            query = query.filter(Company.status == status)
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

        # Get top industries
        top_industries = (
            self.db.query(
                Company.primary_industry, func.count(Company.id).label("count")
            )
            .group_by(Company.primary_industry)
            .order_by(desc("count"))
            .limit(5)
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
                {"industry": industry, "count": count}
                for industry, count in top_industries
            ],
        )

    def _transform_company(self, company: Company) -> CompanyResponse:
        # Calculate overall score
        score = company.qualification_score or self._calculate_default_score(company)

        # Parse qualification details
        qual_details = company.qualification_details or {}
        qualification_score = QualificationScore(
            financialStability=qual_details.get("financial_stability", 75),
            equipmentNeed=qual_details.get("equipment_need", 80),
            timing=qual_details.get("timing", 70),
            decisionAuthority=qual_details.get("decision_authority", 75),
        )

        # Format location
        location = f"{company.location_details or 'Unknown'}, {company.country}"

        # Format last activity
        last_activity = (
            company.created_at.strftime("%Y-%m-%d") if company.created_at else "Unknown"
        )

        return CompanyResponse(
            id=company.id,
            company=company.discovered_name,
            industry=company.primary_industry or "Unknown",
            location=location,
            score=score,
            status=company.status,
            lastActivity=last_activity,
            equipmentNeed=company.equipment_needs
            or self._infer_equipment_need(company),
            estimatedValue=company.estimated_deal_value
            or self._calculate_deal_value(company),
            employees=company.employee_count or self._estimate_employees(company),
            website=company.website_url or company.source_url,
            email=company.contact_email,
            phone=company.contact_phone,
            notes=company.initial_reasoning,
            recentNews=company.recent_news,
            qualificationScore=qualification_score,
        )

    def _calculate_default_score(self, company: Company) -> int:
        # Base score calculation logic
        base_score = 70
        if company.primary_industry in ["Healthcare", "Medical"]:
            base_score += 15
        elif company.primary_industry in ["Beauty & Wellness"]:
            base_score += 10
        return min(base_score, 95)

    def _infer_equipment_need(self, company: Company) -> str:
        industry_equipment = {
            "Healthcare": "Medical Equipment",
            "Beauty & Wellness": "Beauty Equipment",
            "Horeca": "Kitchen Equipment",
        }
        return industry_equipment.get(company.primary_industry, "Equipment")

    def _calculate_deal_value(self, company: Company) -> str:
        # Industry-based deal value estimation
        industry_values = {
            "Healthcare": "€75,000-€125,000",
            "Beauty & Wellness": "€35,000-€65,000",
            "Horeca": "€25,000-€45,000",
        }
        return industry_values.get(company.primary_industry, "€35,000-€75,000")

    def _estimate_employees(self, company: Company) -> str:
        # Default employee estimates by industry
        return "10-50"  # Conservative default
