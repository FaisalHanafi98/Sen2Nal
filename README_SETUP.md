# Sen2Nal: Local Development Setup Guide

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

> **Stock Sentiment + Calendar Signal Analysis System**

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install poetry
poetry install

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Run migrations
poetry run alembic upgrade head

# 4. Start API (Terminal 1)
poetry run uvicorn src.api.main:app --reload

# 5. Start Dashboard (Terminal 2)
poetry run streamlit run src/dashboard/app.py
```

**Access:**
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/api/v1/docs
- Health: http://localhost:8000/api/v1/health

---

## 📋 Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Download](https://docs.docker.com/get-docker/)
- **Git** - [Download](https://git-scm.com/)
- **Make** (optional) - Pre-installed on Linux/Mac, [Windows](http://gnuwin32.sourceforge.net/packages/make.htm)

---

## 📦 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/sen2nal.git
cd sen2nal
```

### 2. Set Up Python Environment

#### Option A: Using Poetry (Recommended)

```bash
# Install Poetry
pip install poetry

# Install all dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### Option B: Using pip + venv

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # (generate from pyproject.toml first)
```

### 3. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env (optional for Phase 0)
# For Phase 0, default values work fine
```

**Important environment variables:**
```env
# Database (default works with docker-compose)
DATABASE_URL=postgresql://sen2nal_user:sen2nal_password@localhost:5432/sen2nal

# API Configuration
API_PORT=8000
STREAMLIT_PORT=8501

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 4. Start PostgreSQL Database

```bash
# Start database
docker-compose up -d postgres

# Verify it's running
docker-compose ps

# Check logs
docker-compose logs postgres
```

**Expected output:**
```
sen2nal-postgres | PostgreSQL init process complete; ready for start up.
sen2nal-postgres | database system is ready to accept connections
```

### 5. Initialize Database Schema

```bash
# Run all migrations
poetry run alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, initial schema
```

### 6. Verify Installation

```bash
# Test database connection
poetry run python -c "from src.database.connection import check_db_connection; print(check_db_connection())"

# Expected: True
```

---

## 🎯 Running the Application

### Method 1: Using Make (Easiest)

```bash
# See all available commands
make help

# Start API server
make run-api

# Start dashboard (in another terminal)
make run-dashboard

# Or see both commands to run separately
make run-all
```

### Method 2: Manual Commands

#### Terminal 1 - API Server

```bash
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Streamlit Dashboard

```bash
poetry run streamlit run src/dashboard/app.py --server.port 8501
```

### Accessing the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | Main user interface |
| **API Docs** | http://localhost:8000/api/v1/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/api/v1/health | System status |
| **pgAdmin** | http://localhost:5050 | Database admin (optional) |

---

## 🧪 Testing

### Run All Tests

```bash
# Using make
make test

# Or directly
poetry run pytest
```

### Run Specific Test Types

```bash
# Unit tests only
make test-unit

# Integration tests
make test-integration

# Browser tests (requires Streamlit running)
make test-browser

# With coverage report
make test-coverage
```

### View Coverage Report

```bash
# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html

# Open in browser
# Windows: start htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
# Mac: open htmlcov/index.html
```

---

## 🛠️ Development Workflow

### Daily Development

```bash
# 1. Start database
make db-up

# 2. Run migrations (if any new ones)
make migrate

# 3. Start API + Dashboard (2 terminals)
make run-api
make run-dashboard

# 4. Make code changes...

# 5. Run tests
make test

# 6. Format code
make format

# 7. Commit changes
git add .
git commit -m "Your message"
```

### Database Management

```bash
# Start PostgreSQL
make db-up

# Stop PostgreSQL
make db-down

# Reset database (⚠️ DELETES ALL DATA)
make db-reset

# Open PostgreSQL shell
make db-shell

# View PostgreSQL logs
make db-logs

# Create new migration
make migrate-create MSG="add new column"

# Run migrations
make migrate

# Rollback last migration
make migrate-rollback

# View migration history
make migrate-history
```

### Code Quality

```bash
# Format code (black + isort)
make format

# Run linters (ruff + mypy)
make lint

# Check formatting without changes
make format-check
```

---

## 🐛 Troubleshooting

### PostgreSQL Connection Failed

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
```bash
# 1. Check if PostgreSQL is running
docker-compose ps

# 2. Restart PostgreSQL
docker-compose restart postgres

# 3. Check logs
docker-compose logs postgres

# 4. Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Port Already in Use

**Problem:** `Address already in use: 8000` or `8501`

**Solutions:**
```bash
# Find process using the port
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Kill the process
# Windows:
taskkill /PID <PID> /F

# Linux/Mac:
kill -9 <PID>
```

### Alembic Migration Errors

**Problem:** `alembic.util.exc.CommandError: Can't locate revision identified by 'xxx'`

**Solutions:**
```bash
# 1. Check migration history
poetry run alembic history

# 2. Check current revision
poetry run alembic current

# 3. Reset to specific revision
poetry run alembic downgrade <revision>

# 4. Recreate database if needed
make db-reset
```

### Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solutions:**
```bash
# 1. Ensure you're in project root
pwd

# 2. Reinstall dependencies
poetry install

# 3. Check PYTHONPATH
echo $PYTHONPATH  # Linux/Mac
echo %PYTHONPATH%  # Windows

# 4. Run with poetry
poetry run python your_script.py
```

### Docker Compose Errors

**Problem:** `ERROR: Couldn't connect to Docker daemon`

**Solutions:**
```bash
# 1. Start Docker Desktop (Windows/Mac)

# 2. Check Docker status
docker ps

# 3. Restart Docker service
# Windows: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

---

## 📚 Useful Commands

### Database

```bash
# Backup database
docker-compose exec postgres pg_dump -U sen2nal_user sen2nal > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U sen2nal_user -d sen2nal

# Connect to PostgreSQL
docker-compose exec postgres psql -U sen2nal_user -d sen2nal

# List tables
\dt

# Describe table
\d table_name

# Exit
\q
```

### Python

```bash
# Open Python shell with imports
poetry run ipython

# Run Jupyter notebook
poetry run jupyter notebook

# Install new package
poetry add package-name

# Install dev package
poetry add --group dev package-name

# Update dependencies
poetry update
```

### Git

```bash
# Check status
git status

# View changes
git diff

# Create branch
git checkout -b feature-name

# Commit changes
git add .
git commit -m "Description"

# Push changes
git push origin branch-name
```

---

## 🚧 Known Issues (Phase 0)

- [ ] API keys not required yet (Phase 1)
- [ ] No actual data ingestion (Phase 1)
- [ ] Dashboard is placeholder (Phase 3)
- [ ] No tests for API routers yet (will add in Phase 3)

---

## 📖 Next Steps

1. ✅ Complete Phase 0 setup (you are here!)
2. ⏭️ **Phase 1**: Implement data pipeline
3. ⏭️ **Phase 2**: Build scoring engine
4. ⏭️ **Phase 3**: Create full dashboard
5. ⏭️ **Phase 4**: Run experiment & polish

---

## 💡 Tips

- **Use Make**: Simplifies common tasks (`make help` to see all)
- **Check logs**: `logs/sen2nal_*.log` for debugging
- **Hot reload**: API and Dashboard auto-reload on code changes
- **pgAdmin**: Optional database GUI at http://localhost:5050
- **Documentation**: All specs in docs/ folder

---

## 🆘 Getting Help

- Check [SEN2NAL_TECHNICAL_ARCHITECTURE.md](SEN2NAL_TECHNICAL_ARCHITECTURE.md) for design
- Check [SEN2NAL_DATABASE_SCHEMA.md](SEN2NAL_DATABASE_SCHEMA.md) for database
- Check logs in `logs/` directory
- Use `make help` for available commands

---

**Happy Coding! 🚀**
