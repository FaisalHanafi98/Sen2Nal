# Sen2Nal MCP Integration Guide

> **Version**: 1.0.0
> **Date**: 2026-01-12
> **Purpose**: Document MCP tools usage patterns for Sen2Nal development

---

## MCP Priority Rule

Following the Root Orchestrator's MCP-First approach:

```
1. Check if MCP tool exists for the task
2. Use MCP tool if available
3. Fall back to Claude built-in tools only if no MCP available
```

---

## Required MCPs for Sen2Nal

### Tier 1: Critical (Must Have)

| MCP | Purpose | Installation | Use Case |
|-----|---------|--------------|----------|
| **Git MCP** | Version control | Pre-installed | Commits, branches, status |
| **GitHub MCP** | Remote repository | Pre-installed | PRs, issues, file sync |
| **Filesystem MCP** | File operations | Pre-installed | Directory trees, file metadata |
| **Context7 MCP** | Documentation | Pre-installed | FastAPI, Streamlit, XGBoost docs |

### Tier 2: Recommended (Enhance Development)

| MCP | Purpose | Installation | Use Case |
|-----|---------|--------------|----------|
| **PostgreSQL MCP** | Database operations | `npx @anthropic/mcp install postgres` | Direct SQL queries, schema inspection |
| **Jupyter MCP** | ML experimentation | `npx @anthropic/mcp install jupyter` | FinBERT fine-tuning, model experiments |
| **Memory MCP** | Session persistence | `npx @anthropic/mcp install memory` | Cache embeddings, model states |
| **Sequential Thinking MCP** | Complex reasoning | `npx @anthropic/mcp install sequential-thinking` | ML pipeline orchestration |

### Tier 3: Optional (Nice to Have)

| MCP | Purpose | Installation | Use Case |
|-----|---------|--------------|----------|
| **Brave Search MCP** | Real-time search | `npx @anthropic/mcp install brave-search` | News headline fetching |
| **Fetch MCP** | HTTP requests | `npx @anthropic/mcp install fetch` | API calls to Alpha Vantage, Reddit |

---

## MCP Usage Patterns by Agent

### Agent 1: Data Ingestion Agent

```
TASK: Fetch stock data from Alpha Vantage

MCP CHECK:
├── Fetch MCP available? → Use mcp__fetch__* for HTTP requests
├── Brave Search MCP available? → Use for news headlines
└── Neither available? → Use Python requests library

EXAMPLE:
# If Fetch MCP installed:
mcp__fetch__fetch(url="https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL")

# Fallback:
Bash: python -c "import requests; print(requests.get(url).json())"
```

### Agent 2: Sentiment Analysis Agent

```
TASK: Look up FinBERT documentation

MCP CHECK:
├── Context7 MCP available? → Use for HuggingFace transformers docs
└── Not available? → Use WebFetch tool

EXAMPLE:
# With Context7 MCP:
mcp__plugin_context7_context7__resolve-library-id(libraryName="transformers", query="FinBERT sentiment classification")
mcp__plugin_context7_context7__query-docs(libraryId="/huggingface/transformers", query="AutoModelForSequenceClassification")

# Fallback:
WebFetch: https://huggingface.co/docs/transformers
```

### Agent 3: Calendar Pattern Agent

```
TASK: Check pandas documentation for date operations

MCP CHECK:
├── Context7 MCP available? → Query pandas docs
└── Not available? → Use WebFetch

EXAMPLE:
mcp__plugin_context7_context7__resolve-library-id(libraryName="pandas", query="trading calendar business days")
```

### Agent 4: Feature Engineering Agent

```
TASK: Look up XGBoost documentation

MCP CHECK:
├── Context7 MCP available? → Query XGBoost docs
└── Not available? → Use WebFetch

EXAMPLE:
mcp__plugin_context7_context7__resolve-library-id(libraryName="xgboost", query="feature importance SHAP")
```

### Agent 5: Prediction Agent

```
TASK: Run Jupyter notebook for model training

MCP CHECK:
├── Jupyter MCP available? → Execute notebook cells directly
└── Not available? → Use Bash to run jupyter nbconvert

EXAMPLE:
# With Jupyter MCP:
mcp__jupyter__execute_cell(notebook="model_training.ipynb", cell=5)

# Fallback:
Bash: jupyter nbconvert --execute --to notebook model_training.ipynb
```

### Agent 6: Database Agent

```
TASK: Execute SQL query on PostgreSQL

MCP CHECK:
├── PostgreSQL MCP available? → Use for direct queries
└── Not available? → Use Bash with psql or Python SQLAlchemy

EXAMPLE:
# With PostgreSQL MCP:
mcp__postgres__query(sql="SELECT * FROM fact_sentiment WHERE date = CURRENT_DATE")

# Fallback:
Bash: psql -d sen2nal_db -c "SELECT * FROM fact_sentiment WHERE date = CURRENT_DATE"
```

### Agent 7: Dashboard Agent

```
TASK: Look up Streamlit documentation

MCP CHECK:
├── Context7 MCP available? → Query Streamlit docs
├── Playwright MCP available? → Test dashboard visually
└── Neither available? → Use WebFetch, manual testing

EXAMPLE:
mcp__plugin_context7_context7__resolve-library-id(libraryName="streamlit", query="caching data st.cache_data")
```

---

## Git Operations (Always Use MCP)

### Status Check
```
# ALWAYS use Git MCP:
mcp__git__git_status(path="C:/Users/asbou/OneDrive/Desktop/Work/Development/Sen2Nal")
```

### Commit Changes
```
# ALWAYS use Git MCP:
mcp__git__git_add(path=".", files=".")
mcp__git__git_commit(path=".", message="feat(sentiment): implement FinBERT scoring pipeline")
```

### Branch Operations
```
# ALWAYS use Git MCP:
mcp__git__git_branch(path=".", mode="create", branchName="feature/finbert-integration")
mcp__git__git_checkout(path=".", branchOrPath="feature/finbert-integration")
```

### View Changes
```
# ALWAYS use Git MCP:
mcp__git__git_diff(path=".", staged=true)
mcp__git__git_log(path=".", maxCount=10)
```

---

## GitHub Operations (Always Use MCP)

### Push to Remote
```
# ALWAYS use GitHub MCP for remote operations:
mcp__git__git_push(path=".", remote="origin", branch="main")
```

### Create Pull Request
```
mcp__github__create_pull_request(
    owner="FaisalHanafi98",
    repo="Sen2Nal",
    title="feat: implement sentiment scoring pipeline",
    head="feature/sentiment-scoring",
    base="main",
    body="## Summary\n- Implemented FinBERT sentiment analysis..."
)
```

### File Operations on GitHub
```
mcp__github__get_file_contents(owner="FaisalHanafi98", repo="Sen2Nal", path="src/scoring/finbert.py")
```

---

## Documentation Lookup Pattern

```python
# Standard pattern for any library lookup:

# Step 1: Resolve library ID
result = mcp__plugin_context7_context7__resolve-library-id(
    libraryName="<library-name>",
    query="<what you want to know>"
)

# Step 2: Query documentation with resolved ID
docs = mcp__plugin_context7_context7__query-docs(
    libraryId="<resolved-library-id>",
    query="<specific question>"
)
```

### Common Library IDs for Sen2Nal

| Library | Context7 ID | Common Queries |
|---------|-------------|----------------|
| FastAPI | `/tiangolo/fastapi` | Dependency injection, middleware |
| Streamlit | `/streamlit/streamlit` | Caching, session state |
| SQLAlchemy | `/sqlalchemy/sqlalchemy` | Async sessions, relationships |
| XGBoost | `/dmlc/xgboost` | Feature importance, hyperparameters |
| Transformers | `/huggingface/transformers` | FinBERT, tokenization |
| Pandas | `/pandas-dev/pandas` | DataFrame operations |
| Plotly | `/plotly/plotly.py` | Interactive charts |

---

## MCP Decision Tree

```
┌─ Task Type ─────────────────────────────────────────────────────┐
│                                                                  │
│  Git Operations?                                                 │
│  └── YES → mcp__git__* (ALWAYS)                                 │
│                                                                  │
│  GitHub Operations?                                              │
│  └── YES → mcp__github__* (ALWAYS)                              │
│                                                                  │
│  Documentation Lookup?                                           │
│  └── YES → mcp__plugin_context7_context7__* (ALWAYS)            │
│                                                                  │
│  File Tree/Metadata?                                             │
│  └── YES → mcp__filesystem__* (prefer over ls)                  │
│                                                                  │
│  Database Query?                                                 │
│  └── PostgreSQL MCP installed?                                   │
│      ├── YES → mcp__postgres__*                                 │
│      └── NO → Bash: psql or Python SQLAlchemy                   │
│                                                                  │
│  ML Experiment?                                                  │
│  └── Jupyter MCP installed?                                      │
│      ├── YES → mcp__jupyter__*                                  │
│      └── NO → Bash: jupyter commands                            │
│                                                                  │
│  Web Scraping?                                                   │
│  └── Playwright MCP available?                                   │
│      ├── YES → mcp__playwright__*                               │
│      └── NO → Python requests/BeautifulSoup                     │
│                                                                  │
│  AWS Operations?                                                 │
│  └── YES → mcp__aws__* (ALWAYS)                                 │
│                                                                  │
│  Default: Use Claude built-in tools (Read, Write, Edit, Bash)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Installation Commands

### Check Installed MCPs
```bash
# List all configured MCP servers (check Claude Code settings)
cat ~/.config/claude-code/settings.json | jq '.mcpServers'
```

### Install Recommended MCPs
```bash
# PostgreSQL MCP (for database operations)
npx @anthropic/mcp install @anthropic/mcp-server-postgres

# Jupyter MCP (for ML experiments)
npx @anthropic/mcp install @anthropic/mcp-server-jupyter

# Memory MCP (for session persistence)
npx @anthropic/mcp install @anthropic/mcp-server-memory

# Brave Search MCP (for news fetching)
npx @anthropic/mcp install @anthropic/mcp-server-brave-search
```

---

## Error Handling with MCPs

```
IF MCP call fails:
├── Check if MCP is installed and configured
├── Verify parameters are correct
├── Log the error
├── Fall back to alternative method
└── Continue with task
```

### Example Fallback Pattern
```python
# Pseudo-code for MCP fallback
try:
    # Try MCP first
    result = mcp__postgres__query(sql="SELECT * FROM stocks")
except MCPNotAvailable:
    # Fall back to Bash
    result = bash("psql -d sen2nal_db -c 'SELECT * FROM stocks'")
except MCPError as e:
    # Log and try Python
    log_error(e)
    result = python_sqlalchemy_query("SELECT * FROM stocks")
```

---

## Sen2Nal Specific MCP Configuration

Add to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-postgres"],
      "env": {
        "POSTGRES_URL": "postgresql://user:pass@localhost:5432/sen2nal_db"
      }
    },
    "jupyter": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-jupyter"],
      "env": {
        "JUPYTER_PATH": "./notebooks"
      }
    }
  }
}
```

---

*Document generated: 2026-01-12*
*Based on: Root CLAUDE.md MCP Utilization Priority section*
