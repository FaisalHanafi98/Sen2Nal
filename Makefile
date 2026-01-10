.PHONY: help install dev-install setup db-up db-down db-reset migrate test lint format clean run-api run-dashboard run-all

# Variables
PYTHON := python
POETRY := poetry
DOCKER_COMPOSE := docker-compose

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Sen2Nal - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Installation & Setup
# =============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(POETRY) install --no-dev

dev-install: ## Install all dependencies including dev tools
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)Installing Playwright browsers...$(NC)"
	$(POETRY) run playwright install chromium

setup: dev-install db-up migrate seed ## Complete local development setup
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "$(YELLOW)Run 'make run-all' to start API and Dashboard$(NC)"

# =============================================================================
# Database Management
# =============================================================================

db-up: ## Start PostgreSQL database
	@echo "$(BLUE)Starting PostgreSQL...$(NC)"
	$(DOCKER_COMPOSE) up -d postgres
	@sleep 3
	@echo "$(GREEN)✓ PostgreSQL is running$(NC)"

db-down: ## Stop PostgreSQL database
	@echo "$(BLUE)Stopping PostgreSQL...$(NC)"
	$(DOCKER_COMPOSE) down

db-reset: db-down db-up migrate ## Reset database (WARNING: deletes all data)
	@echo "$(YELLOW)Database has been reset$(NC)"

db-shell: ## Open PostgreSQL shell
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	$(DOCKER_COMPOSE) exec postgres psql -U sen2nal_user -d sen2nal

db-logs: ## Show PostgreSQL logs
	$(DOCKER_COMPOSE) logs -f postgres

# =============================================================================
# Database Migrations
# =============================================================================

migrate: ## Run all pending migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	$(POETRY) run alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	@echo "$(BLUE)Creating new migration...$(NC)"
	$(POETRY) run alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back migration...$(NC)"
	$(POETRY) run alembic downgrade -1

migrate-history: ## Show migration history
	$(POETRY) run alembic history

# =============================================================================
# Data Seeding
# =============================================================================

seed: ## Seed database with initial data
	@echo "$(BLUE)Seeding database...$(NC)"
	$(POETRY) run python scripts/seed_database.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

# =============================================================================
# Running Services
# =============================================================================

run-api: ## Run FastAPI server
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	$(POETRY) run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard: ## Run Streamlit dashboard
	@echo "$(BLUE)Starting Streamlit dashboard...$(NC)"
	$(POETRY) run streamlit run src/dashboard/app.py --server.port 8501

run-all: ## Run both API and Dashboard (requires separate terminals)
	@echo "$(YELLOW)Run these commands in separate terminals:$(NC)"
	@echo "  Terminal 1: $(GREEN)make run-api$(NC)"
	@echo "  Terminal 2: $(GREEN)make run-dashboard$(NC)"

run-pipeline: ## Run data pipeline manually
	@echo "$(BLUE)Running data pipeline...$(NC)"
	$(POETRY) run python scripts/run_pipeline.py

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(POETRY) run pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(POETRY) run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(POETRY) run pytest tests/integration/ -v

test-browser: ## Run browser tests (requires Streamlit running)
	@echo "$(BLUE)Running browser tests...$(NC)"
	$(POETRY) run pytest tests/browser/ -v --headed

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(POETRY) run pytest --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	$(POETRY) run pytest-watch

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	$(POETRY) run ruff check src/ tests/
	$(POETRY) run mypy src/

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(POETRY) run black src/ tests/ scripts/
	$(POETRY) run isort src/ tests/ scripts/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(POETRY) run black --check src/ tests/ scripts/
	$(POETRY) run isort --check-only src/ tests/ scripts/

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean db-down ## Clean everything including Docker volumes
	@echo "$(YELLOW)Removing Docker volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

# =============================================================================
# Development Utilities
# =============================================================================

shell: ## Open Python shell with imports
	$(POETRY) run ipython

notebook: ## Start Jupyter notebook server
	$(POETRY) run jupyter notebook notebooks/

logs-api: ## Tail API logs
	tail -f logs/sen2nal_*.log

health: ## Check if services are healthy
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | jq '.' || echo "$(RED)API not responding$(NC)"
	@curl -s http://localhost:8501/_stcore/health | jq '.' || echo "$(RED)Streamlit not responding$(NC)"

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

# =============================================================================
# Default target
# =============================================================================

.DEFAULT_GOAL := help
