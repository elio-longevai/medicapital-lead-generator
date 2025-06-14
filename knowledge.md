# MediCapital Lead Generation Engine

## Project Overview
AI-powered lead generation system for MediCapital Solutions that discovers and qualifies B2B prospects in healthcare, beauty & wellness, and horeca industries across Netherlands and Belgium.

## Architecture
- **Backend**: Python FastAPI with SQLAlchemy, LangGraph workflows, Google Gemini AI
- **Frontend**: React TypeScript with Vite, TailwindCSS, shadcn/ui components
- **Database**: SQLite (development), PostgreSQL-ready for production
- **AI**: LangChain + LangGraph for multi-step lead qualification workflows

## Key Commands
- `make run-api` - Start FastAPI backend server (port 8000)
- `make frontend-dev` - Start frontend dev server (port 5173)
- `make run` - Run lead generation for Netherlands
- `make create-db` - Initialize database tables
- `make setup` - Full development environment setup

## Development Workflow
1. Backend API runs on port 8000 with auto-reload
2. Frontend connects to backend via React Query hooks
3. Database migration handled by `migrate_db.py`
4. Lead generation uses LangGraph workflows with AI qualification

## Target Industries
- Healthcare: Medical devices, diagnostic equipment
- Beauty & Wellness: Laser systems, wellness equipment  
- Horeca: Kitchen robotics, hospitality equipment

## API Integration
- Frontend uses `useCompanies()`, `useDashboardStats()` hooks
- Real-time data from SQLite database via FastAPI
- Status mapping: "qualified", "in_review", "discovered"
- Enhanced company data with contact info, deal values, equipment needs

## Environment Setup
- Requires `.env` file with API keys (Google, Brave, LangSmith)
- Uses `uv` for Python dependency management
- Bun for frontend package management
