# ====================================================================================
#  Makefile for MediCapital Lead Generation Engine
#
#  This Makefile standardizes development tasks. To get started, run `make setup`.
#  To see all available commands, run `make help`.
# ====================================================================================

.PHONY: help install install-backend install-frontend compile-requirements clean test run-backend run-api lint format setup setup-pre-commit vulture create-db start-scheduler run-frontend frontend-build frontend-lint

# --- Variables ---
# Customize these for your project
PYTHON 				:= python3
VENV 				:= .venv
PIP 				:= $(VENV)/bin/pip
PYTEST 			    := $(VENV)/bin/pytest
UV 					:= uv

# ====================================================================================
#  📚 Help & Project Standards
# ====================================================================================

help:
	@printf "\n\033[1m🚀 MediCapital Lead Generation Engine - Available Commands:\033[0m\n\n"
	@printf "  \033[36m%-25s\033[0m %s\n" "make setup" "🛠️  Run this first! Installs uv, cleans, installs deps, and sets up git hooks."
	@printf "\n\033[1m--- Installation ---\033[0m\n"
	@printf "  \033[36m%-25s\033[0m %s\n" "make install" "📦 Install all backend and frontend dependencies."
	@printf "  \033[36m%-25s\033[0m %s\n" "make install-backend" "📦 Install backend dependencies."
	@printf "  \033[36m%-25s\033[0m %s\n" "make install-frontend" "📦 Install frontend dependencies."
	@printf "  \033[36m%-25s\033[0m %s\n" "make compile-requirements" "📝 Lock new dependencies from requirements.in to requirements.txt."
	@printf "\n\033[1m--- Running the Application ---\033[0m\n"
	@printf "  \033[36m%-25s\033[0m %s\n" "make run-backend" "🚀 Run lead generation for Netherlands."
	@printf "  \033[36m%-25s\033[0m %s\n" "make run-frontend" "🚀 Start frontend development server."
	@printf "  \033[36m%-25s\033[0m %s\n" "make run-api" "🌐 Start the FastAPI backend server."
	@printf "  \033[36m%-25s\033[0m %s\n" "make start-scheduler" "⏰ Start automated scheduler (4-hour intervals)."
	@printf "\n\033[1m--- Database ---\033[0m\n"
	@printf "  \033[36m%-25s\033[0m %s\n" "make create-db" "🗄️  Initialize the database tables."
	@printf "\n\033[1m--- Code Quality ---\033[0m\n"
	@printf "  \033[36m%-25s\033[0m %s\n" "make test" "🧪 Run the entire test suite with pytest."
	@printf "  \033[36m%-25s\033[0m %s\n" "make format" "✨ Automatically format code to match project style."
	@printf "  \033[36m%-25s\033[0m %s\n" "make lint" "🔍 Check code for potential errors and style issues."
	@printf "  \033[36m%-25s\033[0m %s\n" "make vulture" "🦅 Hunt for and report unused (dead) code."
	@printf "\n\033[1m--- Housekeeping ---\033[0m\n"
	@printf "  \033[36m%-25s\033[0m %s\n" "make clean" "🧹 Remove all cache files, build artifacts, and the virtual env."
	@printf "\n\033[1;32m--- How to Reuse This Makefile ---\033[0m\n"
	@printf "This Makefile is a template for excellent programming standards. To use it in a new project:\n"
	@printf "  1. Copy this \033[3mMakefile\033[0m to your project root.\n"
	@printf "  2. Adjust the variables under the '--- Variables ---' section if needed.\n"
	@printf "  3. Ensure you have a \033[3mrequirements.in\033[0m file without versions for your directly imported dependencies.\n"
	@printf "  4. Run \033[3mmake setup\033[0m to initialize your environment (includes uv installation).\n"
	@printf "  5. Follow the development workflow: code, \033[3mmake format\033[0m, \033[3mmake lint\033[0m, \033[3mmake test\033[0m, then commit!\n\n"

# ====================================================================================
#  ⚙️ Setup & Installation
# ====================================================================================

install: install-backend install-frontend
	@echo "\n✅ All backend and frontend dependencies are installed!"

install-backend:
	@echo "\n📦 Installing backend dependencies..."
	@echo "--> Step 1: Creating a fresh virtual environment at '$(VENV)'..."
	@$(UV) venv $(VENV) --seed
	@echo "--> Step 2: Installing project dependencies from 'requirements.txt'..."
	@$(UV) pip install -r requirements.txt
	@echo " -> Step 3: Installing essential development tools (ruff, pre-commit, vulture, uvicorn)..."
	@$(UV) pip install --python $(VENV)/bin/python pre-commit vulture ruff pytest pytest-cov uvicorn[standard]
	@echo "\n✅ Backend dependencies installed successfully!"

compile-requirements:
	@echo "\n📝 Compiling 'requirements.in' to lock dependencies in 'requirements.txt'..."
	@$(UV) pip compile requirements.in -o requirements.txt
	@echo "\n✅ 'requirements.txt' has been updated. Don't forget to commit it!"

setup: clean install setup-pre-commit
	@echo "\n🎉 Hooray! Your development environment is ready to go! 🎉"
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env and add your API keys"
	@echo "  2. Run 'make create-db' to initialize the database"
	@echo "  3. Run 'make run-backend' to test lead generation for Netherlands"
	@echo "  4. Run 'make run-frontend' to start the frontend development server"

# ====================================================================================
#  🎨 Frontend Commands
# ====================================================================================

install-frontend:
	@echo "\n📦 Installing frontend dependencies..."
	@cd frontend && bun install
	@echo "\n✅ Frontend dependencies installed successfully!"

run-frontend:
	@echo "\n🚀 Starting frontend development server..."
	@echo "--> Frontend will be available at http://localhost:8080"
	@cd frontend && bun run dev

frontend-build:
	@echo "\n🏗️  Building frontend for production..."
	@cd frontend && bun run build
	@echo "\n✅ Frontend build complete!"

frontend-lint:
	@echo "\n🔍 Linting frontend code..."
	@cd frontend && bun run lint
	@echo "\n✅ Frontend linting complete!"

# ====================================================================================
#  🧹 Housekeeping
# ====================================================================================

clean:
	@echo "\n🧹 Sweeping away cache, build artifacts, and the virtual environment..."
	@rm -rf $(VENV)
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@rm -f medicapital.db
	@cd frontend && rm -rf node_modules dist .vite
	@echo "\n✅ Project is sparkling clean!"

# ====================================================================================
#  🗄️ Database Management
# ====================================================================================

create-db:
	@echo "\n🗄️  Initializing database tables..."
	@cd backend && PYTHONPATH=. ../$(VENV)/bin/python -m app.main create-db
	@echo "\n✅ Database is ready for lead generation!"

# ====================================================================================
#  🚀 Lead Generation Operations
# ====================================================================================

run-backend:
	@echo "\n🇳🇱 Running lead generation for Netherlands..."
	@echo "--> This will discover and qualify B2B leads in the Netherlands"
	@echo "--> Rate limited to 1 search per second to respect API limits"
	@cd backend && PYTHONPATH=. ../$(VENV)/bin/python -m app.main run-once --country NL

run-test:
	@echo "\n🧪 Running short test of lead generation pipeline (5 queries)..."
	@cd backend && PYTHONPATH=. ../$(VENV)/bin/python -m app.main run-once --country NL --limit 5

run-api:
	@echo "\n🌐 Starting FastAPI backend server..."
	@echo "--> API will be available at http://localhost:8000"
	@echo "--> Press CTRL+C to stop the server"
	@cd backend && PYTHONPATH=. ../$(VENV)/bin/python -m uvicorn app.api_server:app --reload --host 0.0.0.0 --port 8000

start-scheduler:
	@echo "\n⏰ Starting automated lead generation scheduler..."
	@echo "--> Will run every 4 hours, alternating between NL and BE"
	@echo "--> Press CTRL+C to stop the scheduler"
	@cd backend && PYTHONPATH=. ../$(VENV)/bin/python -m app.main start-scheduler --interval-hours 4

# ====================================================================================
#  ✨ Code Quality & Testing
# ====================================================================================

test:
	@echo "\n🧪 Running the test suite with pytest..."
	@$(PYTEST) backend/tests/ -v --cov=backend.app --cov-report=term-missing
	@echo "\n🏁 Test run finished."

lint:
	@echo "\n🔍 Checking code for style issues and potential errors..."
	@echo "--> Running Ruff linter..."
	@ruff check backend/
	@echo "\n🏁 Linting complete."

format:
	@echo "\n✨ Auto-formatting code to match project style..."
	@echo "--> Formatting with Ruff Formatter..."
	@ruff format backend/
	@echo "--> Auto-fixing fixable lint issues with Ruff..."
	@ruff check --fix backend/
	@echo "\n✅ Code formatting complete."

vulture:
	@echo "\n🦅 Hunting for dead code with Vulture..."
	@vulture backend/ --exclude .venv
	@echo "\n🏁 Vulture scan complete."

# ====================================================================================
#  🪝 Git Hooks
# NOTE: For more robust hook management, consider using the pre-commit framework
#       (https://pre-commit.com/) with a `.pre-commit-config.yaml` file.
# ====================================================================================

setup-pre-commit:
	@echo "\n🪝 Setting up Git pre-commit hook..."
	@echo "--> This hook will automatically format and lint before you commit."
	@mkdir -p .git/hooks
	@echo '#!/bin/bash' > .git/hooks/pre-commit
	@echo '# Pre-commit hook to run ruff format, ruff check --fix' >> .git/hooks/pre-commit
	@echo 'set -e' >> .git/hooks/pre-commit
	@echo '' >> .git/hooks/pre-commit
	@echo 'echo "--- Running Pre-Commit Checks ---"' >> .git/hooks/pre-commit
	@echo '# Get list of staged Python files' >> .git/hooks/pre-commit
	@echo 'STAGED_FILES=$$(git diff --cached --name-only --diff-filter=ACM | grep "\.py$$" || true)' >> .git/hooks/pre-commit
	@echo 'if [ -z "$$STAGED_FILES" ]; then' >> .git/hooks/pre-commit
	@echo '    echo "✅ No Python files to check."' >> .git/hooks/pre-commit
	@echo '    exit 0' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo '' >> .git/hooks/pre-commit
	@echo 'echo "✨ Formatting staged files..."' >> .git/hooks/pre-commit
	@echo 'echo "$$STAGED_FILES" | xargs ruff format' >> .git/hooks/pre-commit
	@echo 'echo "🔍 Linting and auto-fixing staged files..."' >> .git/hooks/pre-commit
	@echo 'echo "$$STAGED_FILES" | xargs ruff check --fix' >> .git/hooks/pre-commit
	@echo '' >> .git/hooks/pre-commit
	@echo '# Re-stage the files after formatting/fixing' >> .git/hooks/pre-commit
	@echo 'echo "--> Re-staging modified files..."' >> .git/hooks/pre-commit
	@echo 'echo "$$STAGED_FILES" | xargs git add' >> .git/hooks/pre-commit
	@echo '' >> .git/hooks/pre-commit
	@echo 'echo "--- ✅ Pre-Commit Checks Passed! ---"' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "--> Pre-commit hook has been installed and made executable."
	@echo "\n✅ Git hook setup is complete! It will run automatically on your next \`git commit\`."
