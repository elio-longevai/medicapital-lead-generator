<div align="center">

# 🚀 MediCapital Lead Generation Engine

*AI-Powered B2B Lead Discovery for Equipment Leasing*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-🦜-green.svg)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-🕸️-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini-🤖-orange.svg)](https://ai.google.dev/)

---

*Automatically discovers and qualifies high-quality B2B leads in the Netherlands and Belgium for equipment leasing opportunities using advanced AI workflows.*

</div>

## 🎯 **Overview**

The MediCapital Lead Generation Engine is a sophisticated AI-powered system that autonomously discovers, qualifies, and manages B2B leads for equipment leasing in the Netherlands and Belgium. Built with cutting-edge technologies like LangGraph and Google Gemini, it transforms unstructured market intelligence into actionable sales opportunities.

![Application Dashboard](dashboard-screenshot.png)
*Screenshot of the main application dashboard showing lead discovery and qualification interface*

### **🎪 Key Capabilities**

| Feature | Description |
|---------|-------------|
| 🧠 **AI-Powered Discovery** | Uses Google Gemini to intelligently parse ICPs and generate targeted search strategies |
| 🌍 **Multi-Market Support** | Simultaneously targets Netherlands (NL) and Belgium (BE) markets |
| 🔍 **Smart Deduplication** | Advanced company name normalization prevents duplicate entries |
| ⏰ **Automated Scheduling** | Runs continuously with configurable intervals and country rotation |
| 📊 **Production-Ready** | MongoDB with MongoDB Atlas for scalable, cloud-based data storage |
| 🚀 **High Performance** | Async operations for concurrent web searches and AI processing |

---

## 🧩 **Tech Stack**

| Layer | Technologies |
|-------|-------------|
| **AI & LLM** | ![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange) ![LangChain](https://img.shields.io/badge/LangChain-framework-green) ![LangGraph](https://img.shields.io/badge/LangGraph-workflow-purple) |
| **Backend** | ![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-web%20framework-teal) ![Pydantic](https://img.shields.io/badge/Pydantic-data%20validation-red) ![PyMongo](https://img.shields.io/badge/PyMongo-MongoDB%20driver-green) |
| **Frontend** | ![React](https://img.shields.io/badge/React-UI%20library-blue) ![TypeScript](https://img.shields.io/badge/TypeScript-language-blue) ![Vite](https://img.shields.io/badge/Vite-build%20tool-purple) ![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-styling-cyan) |
| **Database** | ![MongoDB](https://img.shields.io/badge/MongoDB-database-green) ![MongoDB Atlas](https://img.shields.io/badge/MongoDB%20Atlas-cloud-blue) |
| **APIs** | ![Brave Search](https://img.shields.io/badge/Brave%20Search-web%20search-orange) ![Firecrawl](https://img.shields.io/badge/Firecrawl-scraping-red) ![Tavily](https://img.shields.io/badge/Tavily-search-green) |
| **Tooling** | ![UV](https://img.shields.io/badge/uv-package%20manager-blue) ![Bun](https://img.shields.io/badge/Bun-frontend%20tooling-yellow) ![Ruff](https://img.shields.io/badge/Ruff-linting%20%26%20formatting-red) |

---

## 🏗️ **System Architecture**

The system follows a **LangGraph workflow** pattern, processing leads through a series of intelligent nodes that include a refinement loop for comprehensive data enrichment.

```mermaid
graph TD
    A[📝 Raw ICP Text] --> B(🧠 structure_icp);
    B --> C(🔍 generate_search_queries);
    C --> D(🌐 execute_web_search);
    D --> E(🎯 triage_and_extract_leads);
    E --> F(🌐 scrape_and_enrich_companies);
    F --> G{<br/>check_enrichment_completeness};
    G -- "Data is Complete" --> K(💾 save_leads_to_db);
    G -- "Data is Missing" --> H(🔍 generate_refinement_queries);
    H --> I(🌐 execute_refinement_search);
    I --> J(🧩 extract_and_merge_missing_info);
    J --> G;
    K --> L([🏁 END]);

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
    style F fill:#e0f7fa
    style G fill:#f9fbe7
    style H fill:#f3e5f5
    style I fill:#fff3e0
    style J fill:#fce4ec
    style K fill:#f1f8e9
```

### **🔄 Workflow Stages**

1.  **📋 ICP Structuring** - Converts raw business requirements into structured JSON. *(Note: This is a candidate for optimization to run only once.)*
2.  **🎯 Query Generation** - Creates targeted Dutch search queries using strategic patterns.
3.  **🌐 Web Search** - Executes concurrent searches via Brave Search API.
4.  **🤖 AI Triage** - An LLM evaluates each search result for B2B relevance and ICP fit.
5.  ** scraping & Enrichment** - The official company website is scraped, and key data points (contact info, revenue, etc.) are extracted.
6.  **🔎 Completeness Check & Refinement Loop** - The system checks if critical data is missing. If so, it generates and executes new, highly specific search queries to find the missing information, merging it with the existing lead data. The loop specifically targets missing fields such as contact email, phone number, location details, employee count, equipment needs, and recent news to complete company profiles. This loop continues until the lead is sufficiently enriched.
7.  **💾 Database Storage** - Saves unique, enriched leads to the database with smart deduplication.

---

## 📁 **Codebase Structure**

```
medicapital_lead_engine/
├── 📦 app/
│   ├── 🔧 core/
│   │   ├── settings.py      # Configuration management with Pydantic
│   │   └── clients.py       # API clients (Gemini, Brave Search)
│   ├── 🗄️ db/
│   │   ├── mongodb.py       # MongoDB connection management
│   │   ├── mongo_models.py  # Pydantic document models
│   │   └── repositories.py  # Repository pattern for database operations
│   ├── 🕸️ graph/
│   │   ├── state.py         # Pydantic models for workflow state
│   │   ├── prompts.py       # Centralized prompt management
│   │   ├── nodes.py         # Core workflow logic (async)
│   │   └── workflow.py      # LangGraph workflow assembly
│   ├── 🛠️ services/
│   │   └── company_name_normalizer.py  # Smart deduplication logic
│   └── 🚀 main.py           # CLI interface with Typer
├── 📝 prompts/
│   ├── icp.txt              # Ideal Customer Profile definition
│   ├── icp_structuring.txt  # ICP parsing prompt
│   ├── query_generation.txt # Search query generation prompt
│   └── lead_triage.txt      # Lead qualification prompt
├── 🧪 tests/
│   └── test_normalizer.py   # Unit tests
├── ⚙️ pyproject.toml        # Project configuration & dependencies
└── 📖 README.md             # This file
```

### **🧩 Core Components**

#### **🔧 Core Layer (`app/core/`)**
- **`settings.py`** - Centralized configuration using Pydantic Settings
- **`clients.py`** - Clean API wrappers for external services (Gemini LLM, Brave Search)

#### **🗄️ Database Layer (`app/db/`)**
- **`mongodb.py`** - MongoDB connection management and client configuration
- **`mongo_models.py`** - Pydantic document models for MongoDB collections
- **`repositories.py`** - Repository pattern implementation for database operations

#### **🕸️ Workflow Engine (`app/graph/`)**
- **`state.py`** - Pydantic models for type-safe data flow through the workflow
- **`prompts.py`** - Dynamic prompt loading from external files for easy customization
- **`nodes.py`** - Async workflow nodes with concurrent processing capabilities
- **`workflow.py`** - LangGraph workflow orchestration and compilation

#### **🛠️ Services (`app/services/`)**
- **`company_name_normalizer.py`** - Advanced text processing for duplicate prevention

---

## 🚀 **Getting Started**

### **Prerequisites**

- **Python 3.12+** - Download from [python.org](https://www.python.org/downloads/)
- **Bun** - Install from [bun.sh](https://bun.sh/) (for frontend development)
- **uv** - Install from [**astral**.sh/uv](https://astral.sh/uv) (for backend package management)

### **1. Environment Setup**

First, create a `.env` file in the `backend/` directory of the project. You can do this by copying the example values below.

**Required API Keys & Configuration:**
```env
# LangSmith - For observability and debugging
# Get your key from https://smith.langchain.com/
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://eu.api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_key_here"
LANGCHAIN_PROJECT="MediCapital Lead Engine"

# LLM Provider
# Get your key from https://aistudio.google.com/app/apikey
GOOGLE_API_KEY="your_gemini_key_here"

# Search Providers
# The system uses a tiered approach (Firecrawl > Tavily > Brave > Serper).
# Provide keys for as many as you can to increase reliability.
# At least one key is required for the system to run.
FIRECRAWL_API_KEY="your_firecrawl_key_here"
TAVILY_API_KEY="your_tavily_key_here"
BRAVE_API_KEY="your_brave_search_key_here"
SERPER_API_KEY="your_serper_key_here"

# Database - MongoDB
# Get your connection string from MongoDB Atlas
MONGODB_URI="your_mongodb_connection_string"
MONGODB_DATABASE="medicapital"
DB_USER="your_mongodb_username"
DB_PASSWORD="your_mongodb_password"

# Log Level
LOG_LEVEL="INFO"
```

### **2. Installation**

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .[dev]
```

### **3. Database Initialization**

```bash
# Create database tables
python -m app.main create-db
```

### **4. Running the Application**

1. **Backend Setup & Execution:**
   ```bash
   cd backend
   make setup              # Installs uv, creates venv, installs deps
   make create-db          # Initialize database
   make run-api           # Start API server at http://localhost:8000
   ```

2. **Frontend Setup & Execution:**
   ```bash
   cd frontend
   bun install            # Install dependencies
   bun run dev           # Start dev server at http://localhost:8080
   ```

### **5. Lead Generation Commands**

```bash
# Single run for Netherlands
python -m app.main run-once --country NL

# Single run for Belgium  
python -m app.main run-once --country BE

# Start automated scheduler (4-hour intervals)
python -m app.main start-scheduler --interval-hours 4
```

---

## ⚙️ **Configuration**

### **Environment Variables**

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key for AI processing | ✅ |
| `BRAVE_API_KEY` | Brave Search API key for web searches | ✅ |
| `LANGCHAIN_API_KEY` | LangSmith API key for observability | ✅ |
| `MONGODB_URI` | MongoDB connection string (Atlas or local) | ✅ |
| `MONGODB_DATABASE` | MongoDB database name | ❌ (defaults to medicapital) |
| `DB_USER` | MongoDB username | ✅ |
| `DB_PASSWORD` | MongoDB password | ✅ |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | ❌ |

### **Customization**

The system is designed for easy customization:

- **📝 ICP Definition**: Edit `prompts/icp.txt` to modify target customer profile
- **🎯 Search Strategy**: Modify `prompts/query_generation.txt` to adjust search patterns  
- **🤖 Lead Qualification**: Update `prompts/lead_triage.txt` to change qualification criteria

### **Ideal Customer Profiles (ICPs)**

The system currently has **3 active ICPs** configured:

- **sustainability_supplier** (Netherlands) - Sustainability equipment suppliers
- **sustainability_end_user** (Netherlands) - End users of sustainability equipment  
- **healthcare_end_user** (Netherlands) - Healthcare equipment end users

To add a new ICP:

1. Create a new `.txt` file in the `prompts/` directory with your ICP definition
2. Add the new ICP to the `ICP_CONFIG` list in `backend/app/main.py`:
   ```python
   {
       "name": "your_icp_name",
       "country": "NL",  # or "BE"
       "file": "your_icp_file.txt",
   }
   ```

### **API Endpoints**

The FastAPI backend provides the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/companies` | GET | List companies with filtering and pagination |
| `/api/companies/{id}` | GET | Get details for a single company |
| `/api/companies/{id}/status` | PATCH | Update company status |
| `/api/dashboard/stats` | GET | Get dashboard statistics |
| `/health` | GET | Health check endpoint |

---

## 🗄️ **Database Schema**

### **MongoDB Collections**

#### **Companies Collection**

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | MongoDB document identifier |
| `normalized_name` | String | Cleaned company name (indexed for uniqueness) |
| `discovered_name` | String | Original company name as found |
| `source_url` | String | URL where company was first discovered |
| `website_url` | String | The company's official website URL |
| `country` | String(2) | Country code (NL/BE) |
| `primary_industry` | String | Main industry classification |
| `initial_reasoning` | String | AI's initial justification for the lead |
| `status` | String | Lead status (discovered, qualified, etc.) |
| `contact_email` | String | Contact email address |
| `contact_phone` | String | Contact phone number |
| `employee_count` | String | Estimated number of employees |
| `estimated_revenue`| String | Estimated annual revenue |
| `equipment_needs` | String | Notes on potential equipment needs |
| `recent_news` | String | Summary of recent company news |
| `location_details`| String | Full location (city, country) |
| `qualification_score` | Integer | AI-generated score (0-100) on ICP fit |
| `qualification_details` | Object | Detailed breakdown of qualification criteria |
| `enriched_data` | Object | Raw enriched data object from scraping |
| `created_at` | DateTime | Discovery timestamp |
| `updated_at` | DateTime | Last modification timestamp |

#### **Additional Collections**

- **`api_usage`** - Tracks API call statistics by provider and date
- **`search_queries`** - Stores used search queries to prevent duplicates
- **`leads`** - Future collection for lead management workflow

**Indexes:**
- `normalized_name` (unique) - Prevents duplicate companies
- `created_at` (descending) - Optimizes recent lead queries
- `icp_name` - Filters companies by target profile

---

## 🧪 **Testing**

```bash
# Run the full test suite
pytest

# Run a quick, 5-query test of the entire pipeline
make run-test

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_normalizer.py -v
```

---

## 🚀 **Production Deployment**

### **MongoDB Setup**

```bash
# 1. Set up MongoDB Atlas cluster or self-hosted MongoDB
# 2. Configure environment variables
export MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority"
export MONGODB_DATABASE="medicapital"
export DB_USER="your_username"
export DB_PASSWORD="your_password"

# 3. Initialize database with indexes
python -m app.main create-db
```

### **Production Checklist**

- [ ] Configure MongoDB Atlas cluster or self-hosted MongoDB
- [ ] Set up environment variable management (e.g., AWS Secrets Manager)
- [ ] Configure MongoDB connection pooling and SSL/TLS
- [ ] Set up MongoDB monitoring and alerting
- [ ] Configure automated backups (Atlas automatic or mongodump)
- [ ] Deploy with process manager (systemd, Docker, etc.)
- [ ] Configure log aggregation
- [ ] Set up health checks
- [ ] Implement database connection retry logic

---

## 🔧 **Development**

### **Adding New Features**

1. **New Workflow Nodes**: Add to `app/graph/nodes.py` and register in `workflow.py`
2. **Database Changes**: Update models in `app/db/mongo_models.py` and repositories in `repositories.py`
3. **New Prompts**: Add to `prompts/` directory and load in `prompts.py`
4. **API Integrations**: Add clients to `app/core/clients.py`

### **Code Quality**

The codebase follows these principles:
- **🎯 Type Safety**: Full Pydantic models and type hints
- **🔄 Async-First**: Concurrent operations for performance
- **📦 Modular Design**: Clear separation of concerns
- **🧪 Testable**: Dependency injection and mocking support
- **📝 Self-Documenting**: Comprehensive docstrings and comments

---

## 📊 **Performance & Monitoring**

### **Built-in Observability**

- **🔍 LangSmith Integration**: Full workflow tracing and debugging
- **📈 Performance Metrics**: Async operations with timing
- **🚨 Error Handling**: Graceful degradation and retry logic
- **📝 Structured Logging**: Detailed operation logs

### **Performance Characteristics**

- **⚡ Concurrent Processing**: Web searches and AI calls run in parallel
- **🎯 Smart Batching**: Efficient database operations
- **🔄 Async Architecture**: Non-blocking I/O operations
- **💾 Memory Efficient**: Streaming data processing

---

## 🤝 **Contributing**

This is a private project for MediCapital Solutions. For internal development:

1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation as needed
4. Submit pull request for review

---

## 📄 **License**

**Private** - MediCapital Solutions

*This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.*

---

<div align="center">

**Built with ❤️ for MediCapital Solutions**

*Transforming equipment leasing through intelligent lead generation*

</div>
