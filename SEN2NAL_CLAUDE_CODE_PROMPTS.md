# Sen2Nal: Claude Code Session Prompts

**Version:** 1.0  
**Purpose:** Ready-to-use prompts for Claude Code sessions during development  
**Author:** Faisal

---

## Overview

This document contains structured prompts for each development phase. Copy the relevant prompt into a new Claude Code session to get targeted, context-aware assistance.

---

## Phase 0: Foundation (Days 1-5)

### Session 0.1: AWS Infrastructure Setup

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 0 - AWS Infrastructure

## Context
I'm building Sen2Nal, a stock sentiment analysis platform. This is Phase 0 focusing on AWS infrastructure setup.

## Project Background
- Stack: Python 3.11, FastAPI, Streamlit, PostgreSQL, AWS (EC2, RDS, S3)
- Purpose: Combine NLP sentiment (FinBERT) with calendar patterns for stock signals
- Target: S&P 500 stocks, daily updates at 6 AM EST

## Current Phase Goals
1. Set up AWS infrastructure (EC2 t3.medium, RDS PostgreSQL, S3 bucket)
2. Configure security groups and IAM roles
3. Create CloudFormation templates for reproducibility

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]

## Constraints
- Budget: ~$50/month
- Must use free tier where possible
- Single EC2 instance hosting both API and dashboard

## Reference Documents
- PRD: /mnt/project/sen2nal-docs/SEN2NAL_PRD.md
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md

## Expected Deliverables
- CloudFormation templates (VPC, EC2, RDS, S3)
- Setup scripts for EC2 initialization
- Security group configurations
```

---

### Session 0.2: Project Scaffold

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 0 - Project Scaffold

## Context
I'm building Sen2Nal, a stock sentiment analysis platform. AWS infrastructure is ready, now setting up the Python project structure.

## Project Background
- Stack: Python 3.11, FastAPI, Streamlit, SQLAlchemy, Alembic
- NLP: HuggingFace FinBERT (ProsusAI/finbert)
- Database: PostgreSQL 15

## Current Phase Goals
1. Create Python project structure following best practices
2. Set up pyproject.toml with all dependencies
3. Configure SQLAlchemy with Alembic migrations
4. Create basic FastAPI app with health endpoint
5. Create basic Streamlit placeholder

## Project Structure Needed
```
sen2nal/
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── sentiment/
│   ├── calendar/
│   ├── features/
│   ├── models/
│   ├── database/
│   ├── api/
│   └── dashboard/
├── tests/
├── scripts/
└── infrastructure/
```

## Reference Documents
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
- Database Schema: /mnt/project/sen2nal-docs/SEN2NAL_DATABASE_SCHEMA.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

## Phase 1: Data Pipeline (Days 6-12)

### Session 1.1: Data Ingestion

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 1 - Data Ingestion

## Context
I'm building Sen2Nal. Project scaffold is ready, now implementing data ingestion from external APIs.

## Project Background
- Data Sources: Alpha Vantage (news), Yahoo Finance (prices), Reddit (PRAW), NewsAPI
- Storage: Raw data to S3, processed to PostgreSQL
- Schedule: Daily at 6 AM EST

## Current Phase Goals
1. Implement API clients for each data source
2. Handle rate limiting gracefully
3. Store raw JSON in S3 with date partitioning
4. Create robust error handling and retry logic

## API Details
- Alpha Vantage: 5 calls/min, news endpoint
- Yahoo Finance: yfinance library, no auth needed
- Reddit: PRAW library, need client_id/secret
- NewsAPI: 100 requests/day, headlines endpoint

## S3 Structure
```
s3://sen2nal-data/
├── raw/
│   ├── news/YYYY/MM/DD/news_YYYY-MM-DD.json
│   ├── reddit/YYYY/MM/DD/reddit_YYYY-MM-DD.json
│   └── prices/YYYY/MM/DD/prices_YYYY-MM-DD.csv
```

## Reference Documents
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
- PRD Section 4.2: /mnt/project/sen2nal-docs/SEN2NAL_PRD.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

### Session 1.2: Text Processing Pipeline

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 1 - Text Processing

## Context
I'm building Sen2Nal. Data ingestion is working, now implementing text processing pipeline.

## Project Background
- Input: Raw news articles and Reddit posts from S3
- Processing: Clean text, extract tickers, deduplicate
- Output: Processed data ready for sentiment scoring

## Current Phase Goals
1. Text cleaning (HTML removal, normalization)
2. Ticker extraction (match against S&P 500 list)
3. Near-duplicate detection (>90% similarity)
4. Data validation and quality checks

## Processing Steps
1. Load raw JSON from S3
2. Clean text (remove HTML, normalize whitespace)
3. Extract ticker mentions (regex + fuzzy match)
4. Deduplicate using content hash
5. Validate data quality
6. Store in staging tables

## Reference Documents
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
- Database Schema (staging tables): /mnt/project/sen2nal-docs/SEN2NAL_DATABASE_SCHEMA.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

## Phase 2: Scoring Engine (Days 13-19)

### Session 2.1: FinBERT Sentiment Scoring

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 2 - FinBERT Sentiment

## Context
I'm building Sen2Nal. Text processing pipeline is ready, now implementing FinBERT sentiment scoring.

## Project Background
- Model: ProsusAI/finbert from HuggingFace
- Input: Cleaned news articles and Reddit posts
- Output: Sentiment score (-1 to +1) per article, aggregated per stock

## Current Phase Goals
1. Implement FinBERT scorer with batch processing
2. Aggregate sentiment per stock (weighted by recency and source)
3. Calculate sentiment momentum (change from previous day)
4. Store in fact_sentiment table

## Implementation Notes
- Batch size: 16 for efficient GPU/CPU usage
- Truncate text to 512 tokens (FinBERT limit)
- Weight recent articles higher
- News weighted 1.5x vs Reddit 1.0x

## Reference Documents
- Technical Architecture (Algorithm 4.1): /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
- Database Schema: /mnt/project/sen2nal-docs/SEN2NAL_DATABASE_SCHEMA.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

### Session 2.2: Calendar Pattern Analysis

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 2 - Calendar Patterns

## Context
I'm building Sen2Nal. FinBERT scoring is working, now implementing calendar pattern analysis.

## Project Background
- This is MY UNIQUE DIFFERENTIATOR based on trading experience
- Analyze 18-month price history for seasonal patterns
- Key insight: Certain months perform better/worse for specific stocks

## Current Phase Goals
1. Calculate monthly average returns (18-month lookback)
2. Calculate monthly win rates
3. Factor in earnings proximity
4. Convert patterns to calendar score (-1 to +1)

## My Trading Insights to Codify
- September historically weak for tech stocks
- January effect (small caps rally)
- Pre-earnings sentiment decay
- Holiday trading patterns

## Reference Documents
- Technical Architecture (Algorithm 4.2): /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
- PRD Feature F3: /mnt/project/sen2nal-docs/SEN2NAL_PRD.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

### Session 2.3: Signal Combination & Conflict Detection

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 2 - Signal Combination

## Context
I'm building Sen2Nal. NLP and Calendar scoring working, now combining them into final signals.

## Project Background
- Combine NLP score (60% weight) with Calendar score (40% weight)
- Detect when signals conflict (disagree by >0.3)
- Generate final BUY/HOLD/AVOID signals

## Current Phase Goals
1. Implement signal combiner with configurable weights
2. Normalize scores to 0-1 range
3. Detect and flag conflicts
4. Calculate confidence levels
5. Store in fact_sentiment table

## Signal Thresholds
- STRONG_BUY: combined > 0.70
- BUY: 0.55 < combined <= 0.70
- HOLD: 0.45 <= combined <= 0.55
- AVOID: combined < 0.45

## Reference Documents
- Technical Architecture (Algorithm 4.3): /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
- PRD Feature F6: /mnt/project/sen2nal-docs/SEN2NAL_PRD.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

## Phase 3: API & Dashboard (Days 20-26)

### Session 3.1: FastAPI Implementation

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 3 - FastAPI

## Context
I'm building Sen2Nal. Scoring engine complete, now implementing the REST API.

## Project Background
- Framework: FastAPI with Pydantic v2
- Endpoints: stocks, sectors, market, experiment
- Auto-generated docs at /docs and /redoc

## Current Phase Goals
1. Implement all API endpoints per specification
2. Create Pydantic response models
3. Add proper error handling
4. Set up CORS for Streamlit access

## Endpoints to Implement
- GET /api/v1/health
- GET /api/v1/stocks/top10
- GET /api/v1/stocks/{ticker}
- GET /api/v1/stocks/search
- GET /api/v1/sectors
- GET /api/v1/market/fear-greed
- GET /api/v1/experiment

## Reference Documents
- API Reference: /mnt/project/sen2nal-docs/SEN2NAL_API_REFERENCE.md
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

### Session 3.2: Streamlit Dashboard

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 3 - Streamlit Dashboard

## Context
I'm building Sen2Nal. API is working, now implementing the Streamlit dashboard.

## Project Background
- Framework: Streamlit 1.30+
- Charts: Plotly for interactive visualizations
- Multi-page app structure

## Current Phase Goals
1. Dashboard page (Top 10 + Fear/Greed)
2. Stock Analysis page (detail view)
3. Sectors page (aggregation)
4. Experiment page (live comparison)
5. Methodology page (documentation)

## UI Components Needed
- Signal gauge (visual -1 to +1)
- Fear & Greed meter
- Sentiment breakdown cards
- Sector bar chart
- Experiment results table

## CRITICAL: Legal Disclaimers
- Footer disclaimer on EVERY page
- First-time user agreement modal
- Warning banners on signal pages
- See Legal Disclaimer document

## Reference Documents
- PRD (UI Mockups): /mnt/project/sen2nal-docs/SEN2NAL_PRD.md
- Legal Disclaimer: /mnt/project/sen2nal-docs/SEN2NAL_LEGAL_DISCLAIMER.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

## Phase 4: Experiment & Polish (Days 27-40)

### Session 4.1: LLM Experiment Implementation

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 4 - LLM Experiment

## Context
I'm building Sen2Nal. Dashboard working (Beta), now implementing the live experiment.

## Project Background
- Compare Sen2Nal picks vs ChatGPT, Gemini, Grok
- 8-week experiment, weekly picks
- Entry: Monday open, Exit: Friday close

## Current Phase Goals
1. Implement standardized LLM prompt
2. Create experiment tracking table
3. Automate Monday pick generation
4. Automate Friday results calculation
5. Display cumulative results

## LLM APIs
- OpenAI: gpt-4 for ChatGPT
- Google AI: gemini-pro for Gemini
- xAI: grok-1 for Grok

## Experiment Protocol
1. Monday 6:30 AM: Generate Sen2Nal picks (top 3 by score)
2. Monday 6:30 AM: Query each LLM with same prompt
3. Monday 9:30 AM: Record entry prices
4. Friday 4:00 PM: Record exit prices
5. Friday 4:00 PM: Calculate returns, determine winner

## Reference Documents
- PRD (Experiment Protocol): /mnt/project/sen2nal-docs/SEN2NAL_PRD.md
- Future Features (Prompt Transparency): /mnt/project/sen2nal-docs/SEN2NAL_FUTURE_FEATURES.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

### Session 4.2: Testing & Documentation

```markdown
# CLAUDE CODE SESSION: Sen2Nal Phase 4 - Testing

## Context
I'm building Sen2Nal. All features implemented, now adding comprehensive tests and documentation.

## Project Background
- Testing: pytest with coverage
- Documentation: Docstrings, README, API docs

## Current Phase Goals
1. Unit tests for all core modules
2. Integration tests for API endpoints
3. Data quality tests for pipeline
4. Update all documentation
5. Create deployment checklist

## Test Coverage Targets
- src/sentiment/: 90%+
- src/calendar/: 90%+
- src/features/: 85%+
- src/api/: 80%+
- Overall: 80%+

## Reference Documents
- Development Setup: /mnt/project/sen2nal-docs/SEN2NAL_DEVELOPMENT_SETUP.md
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md

## What I Need Help With
[SPECIFY YOUR SPECIFIC TASK HERE]
```

---

## Troubleshooting Sessions

### Session: Bug Fixing

```markdown
# CLAUDE CODE SESSION: Sen2Nal - Bug Fix

## Context
I'm building Sen2Nal and encountered a bug.

## Bug Description
[DESCRIBE THE BUG IN DETAIL]

## Steps to Reproduce
1. [STEP 1]
2. [STEP 2]
3. [STEP 3]

## Expected Behavior
[WHAT SHOULD HAPPEN]

## Actual Behavior
[WHAT ACTUALLY HAPPENS]

## Error Messages
```
[PASTE ERROR MESSAGES HERE]
```

## Relevant Code
```python
[PASTE RELEVANT CODE HERE]
```

## What I've Tried
- [ATTEMPT 1]
- [ATTEMPT 2]

## Reference Documents
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md
```

---

### Session: Performance Optimization

```markdown
# CLAUDE CODE SESSION: Sen2Nal - Performance

## Context
I'm building Sen2Nal and need to optimize performance.

## Current Issue
[DESCRIBE PERFORMANCE PROBLEM]

## Metrics
- Current response time: X seconds
- Target response time: Y seconds
- Bottleneck identified: [COMPONENT]

## Profiling Results
[PASTE PROFILING OUTPUT]

## Reference Documents
- Technical Architecture: /mnt/project/sen2nal-docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md

## What I Need Help With
[SPECIFY OPTIMIZATION GOAL]
```

---

## Quick Reference

### Starting a New Session

1. Copy the relevant prompt above
2. Fill in the `[SPECIFY YOUR SPECIFIC TASK HERE]` section
3. Attach relevant project files if needed
4. Start coding!

### Key Documents to Reference

| Document | When to Reference |
|----------|-------------------|
| PRD | Feature requirements, UI mockups |
| Technical Architecture | Algorithms, data flow, code patterns |
| Database Schema | Table structures, queries |
| API Reference | Endpoint specs, response formats |
| Legal Disclaimer | Disclaimer text, UI implementation |
| Future Features | Deferred features, implementation ideas |

### Remember

⚠️ **Always include legal disclaimers in user-facing components!**

- Footer on every page
- First-time user agreement
- Signal warnings
- Backtest warnings
