from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from .models import CompanyResponse, CompanyListResponse, DashboardStats
from ..db.session import get_db
from ..services.company_service import CompanyService

app = FastAPI(title="MediCapital Lead API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/companies", response_model=CompanyListResponse)
def get_companies(
    skip: int = 0,
    limit: int = 100,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "score",
    db: Session = Depends(get_db),
):
    """Get companies with filtering and pagination"""
    service = CompanyService(db)
    companies = service.get_companies_with_filters(
        skip=skip,
        limit=limit,
        industry=industry,
        status=status,
        country=country,
        search=search,
        sort_by=sort_by,
    )
    return companies


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get a single company by ID"""
    service = CompanyService(db)
    company = service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    service = CompanyService(db)
    return service.get_dashboard_statistics()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
