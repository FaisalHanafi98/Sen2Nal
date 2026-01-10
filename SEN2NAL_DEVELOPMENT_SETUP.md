# Sen2Nal: Development Setup Guide

**Version:** 1.0  
**Author:** Faisal  
**Last Updated:** January 2026

---

## 1. Prerequisites

### 1.1 Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Core runtime |
| PostgreSQL | 15+ | Database |
| Docker | 24+ | Local services |
| Git | 2.40+ | Version control |
| VS Code | Latest | Recommended IDE |

### 1.2 API Keys Required

| Service | Purpose | Get Key At |
|---------|---------|------------|
| Alpha Vantage | News data | https://www.alphavantage.co/support/#api-key |
| NewsAPI | Headlines | https://newsapi.org/register |
| Reddit | PRAW access | https://www.reddit.com/prefs/apps |

### 1.3 Optional (for Production)

| Service | Purpose |
|---------|---------|
| AWS Account | Cloud deployment |
| OpenAI API | ChatGPT comparison |
| Google AI | Gemini comparison |
| xAI | Grok comparison |

---

## 2. Environment Setup

### 2.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/sen2nal.git
cd sen2nal

# Check Python version
python --version  # Should be 3.11+
```

### 2.2 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Verify activation
which python  # Should show venv path
```

### 2.3 Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Or using Poetry (alternative)
pip install poetry
poetry install
```

### 2.4 Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

**`.env` file contents:**

```env
# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_URL=postgresql://sen2nal:sen2nal_dev@localhost:5432/sen2nal_dev

# AWS (optional for local dev)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET=sen2nal-data-dev

# API Keys
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
NEWSAPI_KEY=your-newsapi-key
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=Sen2Nal/1.0

# LLM APIs (for experiment)
OPENAI_API_KEY=your-openai-key
GOOGLE_AI_API_KEY=your-google-ai-key
XAI_API_KEY=your-xai-key

# Server
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501
```

---

## 3. Database Setup

### 3.1 Using Docker (Recommended)

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Verify it's running
docker ps

# Check logs
docker logs sen2nal-postgres
```

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: sen2nal-postgres
    environment:
      POSTGRES_USER: sen2nal
      POSTGRES_PASSWORD: sen2nal_dev
      POSTGRES_DB: sen2nal_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sen2nal"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    container_name: sen2nal-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 3.2 Manual PostgreSQL Setup

```bash
# Create database (if not using Docker)
createdb sen2nal_dev

# Or connect to PostgreSQL and create
psql -U postgres
CREATE DATABASE sen2nal_dev;
CREATE USER sen2nal WITH PASSWORD 'sen2nal_dev';
GRANT ALL PRIVILEGES ON DATABASE sen2nal_dev TO sen2nal;
\q
```

### 3.3 Run Migrations

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

### 3.4 Seed Initial Data

```bash
# Seed S&P 500 stocks and calendar data
python scripts/seed_database.py

# Verify data
python -c "
from src.database.connection import SessionLocal
from src.database.models import Stock

db = SessionLocal()
count = db.query(Stock).count()
print(f'Stocks in database: {count}')
db.close()
"
# Should output: Stocks in database: 503
```

---

## 4. Running the Application

### 4.1 Start API Server

```bash
# Development mode with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the run script
python -m src.api.main
```

**Verify API is running:**
- Open http://localhost:8000/docs for Swagger UI
- Open http://localhost:8000/redoc for ReDoc
- Test health: `curl http://localhost:8000/api/v1/health`

### 4.2 Start Streamlit Dashboard

```bash
# Open new terminal, activate venv, then:
streamlit run src/dashboard/app.py --server.port 8501

# Or with additional config
streamlit run src/dashboard/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --browser.gatherUsageStats false
```

**Verify Dashboard is running:**
- Open http://localhost:8501

### 4.3 Run Both Services (Development)

```bash
# Using Makefile
make dev

# Or manually with two terminals
# Terminal 1:
uvicorn src.api.main:app --reload --port 8000

# Terminal 2:
streamlit run src/dashboard/app.py
```

---

## 5. Running Data Pipeline

### 5.1 Manual Pipeline Execution

```bash
# Run full pipeline once
python scripts/run_pipeline.py

# Run specific stages
python scripts/run_pipeline.py --stage ingest
python scripts/run_pipeline.py --stage process
python scripts/run_pipeline.py --stage score
```

### 5.2 Scheduled Execution (Local)

```bash
# Start scheduler in background
python -m src.ingestion.scheduler &

# Or use cron (Linux/Mac)
crontab -e
# Add: 0 6 * * * cd /path/to/sen2nal && /path/to/venv/bin/python scripts/run_pipeline.py
```

---

## 6. Testing

### 6.1 Run All Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 6.2 Run Specific Tests

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_sentiment.py

# Specific test function
pytest tests/unit/test_sentiment.py::test_finbert_scoring -v
```

### 6.3 Test Configuration

```bash
# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

---

## 7. Development Workflow

### 7.1 Code Style

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/

# Run all formatters (Makefile)
make format
make lint
```

### 7.2 Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

### 7.3 Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

**Commit Message Convention:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance

---

## 8. Jupyter Notebooks

### 8.1 Start Jupyter

```bash
# Start Jupyter Lab
jupyter lab

# Or classic notebook
jupyter notebook

# Open specific notebook
jupyter lab notebooks/01_data_exploration.ipynb
```

### 8.2 Notebook Development

```python
# In notebook, add src to path
import sys
sys.path.insert(0, '..')

# Now you can import project modules
from src.sentiment.finbert_scorer import FinBERTScorer
from src.database.connection import SessionLocal
```

---

## 9. IDE Configuration

### 9.1 VS Code Settings

**`.vscode/settings.json`:**

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    }
}
```

### 9.2 Recommended VS Code Extensions

- Python (Microsoft)
- Pylance
- Black Formatter
- isort
- GitLens
- Docker
- PostgreSQL

---

## 10. Troubleshooting

### 10.1 Common Issues

**Issue: PostgreSQL connection refused**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart container
docker-compose restart postgres

# Check logs
docker logs sen2nal-postgres
```

**Issue: Module not found**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue: API key errors**
```bash
# Verify environment variables are loaded
python -c "import os; print(os.getenv('ALPHA_VANTAGE_API_KEY'))"

# Check .env file exists and has correct values
cat .env | grep API_KEY
```

**Issue: FinBERT model download slow**
```bash
# Pre-download model
python -c "
from transformers import AutoModelForSequenceClassification, AutoTokenizer
AutoTokenizer.from_pretrained('ProsusAI/finbert')
AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')
print('Model downloaded successfully')
"
```

### 10.2 Reset Everything

```bash
# Nuclear option - reset all local data
docker-compose down -v
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
alembic upgrade head
python scripts/seed_database.py
```

---

## 11. Useful Commands

### Makefile Commands

```makefile
# Makefile
.PHONY: dev test lint format clean

dev:
	@echo "Starting development servers..."
	uvicorn src.api.main:app --reload --port 8000 &
	streamlit run src/dashboard/app.py

test:
	pytest --cov=src --cov-report=html

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	alembic upgrade head
	python scripts/seed_database.py

pipeline:
	python scripts/run_pipeline.py
```

### Quick Reference

```bash
# Start everything
make dev

# Run tests
make test

# Format code
make format

# Reset database
make db-reset

# Run pipeline
make pipeline
```

---

## 12. Next Steps

After completing setup:

1. ✅ Verify all services are running
2. ✅ Run the test suite
3. 📖 Read the [Technical Architecture](SEN2NAL_TECHNICAL_ARCHITECTURE.md)
4. 📖 Review the [PRD](SEN2NAL_PRD.md) for feature requirements
5. 🚀 Start with Phase 0 tasks

**Happy Coding! 🎉**
