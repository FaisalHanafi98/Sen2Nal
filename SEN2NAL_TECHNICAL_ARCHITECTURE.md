# Sen2Nal: Technical Architecture Document

**Version:** 1.0  
**Author:** Faisal (Mohamad Faisal Bin Mohd Hanafi)  
**Created:** January 2026  
**Purpose:** Detailed technical implementation guide for developers

---

## 1. System Architecture Overview

### 1.1 Architecture Diagram

```
                                    ┌─────────────────────────────────────┐
                                    │           EXTERNAL APIS             │
                                    │  Alpha Vantage │ Yahoo │ Reddit    │
                                    │  NewsAPI │ Fear & Greed             │
                                    └──────────────────┬──────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         EC2 INSTANCE (t3.medium)                      │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │  INGESTION      │  │  PROCESSING     │  │  SCORING            │   │  │
│  │  │  SERVICE        │  │  SERVICE        │  │  SERVICE            │   │  │
│  │  │  ─────────────  │  │  ─────────────  │  │  ─────────────────  │   │  │
│  │  │  • APScheduler  │  │  • Text Clean   │  │  • FinBERT          │   │  │
│  │  │  • API Clients  │  │  • Ticker Extract│ │  • Calendar Calc    │   │  │
│  │  │  • Rate Limiter │  │  • Deduplication│  │  • Signal Combine   │   │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘   │  │
│  │           │                    │                       │              │  │
│  │           └────────────────────┼───────────────────────┘              │  │
│  │                                ▼                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      FASTAPI SERVER (:8000)                     │  │  │
│  │  │  /api/v1/stocks │ /api/v1/sectors │ /api/v1/experiment         │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                │                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    STREAMLIT DASHBOARD (:8501)                  │  │  │
│  │  │  Dashboard │ Stock Detail │ Sectors │ Experiment │ Methodology │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                    │                                    │                    │
│                    ▼                                    ▼                    │
│  ┌─────────────────────────────┐      ┌─────────────────────────────────┐  │
│  │         S3 BUCKET           │      │         RDS POSTGRESQL          │  │
│  │  ─────────────────────────  │      │  ───────────────────────────    │  │
│  │  sen2nal-data/              │      │  • dim_stocks                   │  │
│  │  ├── raw/                   │      │  • dim_calendar                 │  │
│  │  │   ├── news/YYYY/MM/DD/   │      │  • fact_sentiment               │  │
│  │  │   ├── reddit/YYYY/MM/DD/ │      │  • fact_prices                  │  │
│  │  │   └── prices/YYYY/MM/DD/ │      │  • fact_predictions             │  │
│  │  ├── processed/             │      │  • fact_experiment              │  │
│  │  └── models/                │      │  • dim_fear_greed               │  │
│  └─────────────────────────────┘      └─────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Ingestion Service** | Fetch data from external APIs | Python, aiohttp, APScheduler |
| **Processing Service** | Clean, dedupe, extract | Python, NLTK, spaCy |
| **Scoring Service** | Generate sentiment scores | FinBERT, XGBoost |
| **FastAPI Server** | REST API for data access | FastAPI, Pydantic |
| **Streamlit Dashboard** | User interface | Streamlit, Plotly |
| **S3 Bucket** | Raw data lake | AWS S3 |
| **RDS PostgreSQL** | Structured data warehouse | PostgreSQL 15 |

---

## 2. Project Structure

```
sen2nal/
├── README.md
├── pyproject.toml                    # Dependencies (Poetry/pip)
├── Makefile                          # Common commands
├── docker-compose.yml                # Local development
├── .env.example                      # Environment variables template
├── .gitignore
│
├── infrastructure/                   # AWS CloudFormation/scripts
│   ├── cloudformation/
│   │   ├── main.yaml                 # Master stack
│   │   ├── vpc.yaml                  # Network configuration
│   │   ├── ec2.yaml                  # Compute instance
│   │   ├── rds.yaml                  # Database
│   │   └── s3.yaml                   # Storage buckets
│   └── scripts/
│       ├── setup_ec2.sh              # EC2 initialization
│       ├── deploy.sh                 # Deployment script
│       └── backup_db.sh              # Database backup
│
├── notebooks/                        # Jupyter notebooks for analysis
│   ├── 01_data_exploration.ipynb
│   ├── 02_sentiment_analysis.ipynb
│   ├── 03_calendar_patterns.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_model_training.ipynb
│   └── 06_backtesting.ipynb
│
├── src/
│   ├── __init__.py
│   ├── config.py                     # Configuration management
│   ├── constants.py                  # Project constants
│   │
│   ├── ingestion/                    # Data ingestion layer
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract base class
│   │   ├── news_client.py            # Alpha Vantage, NewsAPI
│   │   ├── reddit_client.py          # PRAW wrapper
│   │   ├── price_client.py           # yfinance wrapper
│   │   ├── fear_greed_client.py      # F&G scraper
│   │   ├── scheduler.py              # APScheduler configuration
│   │   └── rate_limiter.py           # API rate limiting
│   │
│   ├── processing/                   # Data processing layer
│   │   ├── __init__.py
│   │   ├── text_cleaner.py           # NLP preprocessing
│   │   ├── ticker_extractor.py       # Entity recognition
│   │   ├── deduplicator.py           # Near-duplicate detection
│   │   └── data_validator.py         # Data quality checks
│   │
│   ├── sentiment/                    # Sentiment analysis
│   │   ├── __init__.py
│   │   ├── finbert_scorer.py         # HuggingFace FinBERT
│   │   ├── ensemble.py               # Source-weighted combination
│   │   └── confidence.py             # Confidence calculation
│   │
│   ├── calendar/                     # Calendar pattern analysis
│   │   ├── __init__.py
│   │   ├── seasonal_patterns.py      # Monthly/quarterly effects
│   │   ├── historical_analyzer.py    # Pattern detection
│   │   └── earnings_tracker.py       # Earnings date tracking
│   │
│   ├── features/                     # Feature engineering
│   │   ├── __init__.py
│   │   ├── nlp_features.py           # Sentiment-derived features
│   │   ├── calendar_features.py      # Time-based features
│   │   ├── signal_combiner.py        # Combine NLP + Calendar
│   │   └── conflict_detector.py      # Detect signal conflicts
│   │
│   ├── models/                       # ML models
│   │   ├── __init__.py
│   │   ├── trainer.py                # XGBoost training
│   │   ├── predictor.py              # Inference wrapper
│   │   └── explainer.py              # SHAP integration
│   │
│   ├── database/                     # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py             # SQLAlchemy engine
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── repositories.py           # Data access layer
│   │   └── migrations/               # Alembic migrations
│   │       ├── versions/
│   │       └── env.py
│   │
│   ├── api/                          # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── dependencies.py           # Dependency injection
│   │   ├── schemas.py                # Pydantic models
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── stocks.py
│   │       ├── sectors.py
│   │       ├── market.py
│   │       └── experiment.py
│   │
│   └── dashboard/                    # Streamlit application
│       ├── __init__.py
│       ├── app.py                    # Main Streamlit entry
│       ├── pages/
│       │   ├── 1_📊_Dashboard.py
│       │   ├── 2_🔍_Stock_Analysis.py
│       │   ├── 3_🏭_Sectors.py
│       │   ├── 4_🧪_Experiment.py
│       │   └── 5_📖_Methodology.py
│       └── components/
│           ├── signal_gauge.py
│           ├── sentiment_card.py
│           ├── calendar_card.py
│           ├── fear_greed_meter.py
│           ├── sector_chart.py
│           └── experiment_table.py
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── unit/
│   │   ├── test_text_cleaner.py
│   │   ├── test_ticker_extractor.py
│   │   ├── test_sentiment.py
│   │   ├── test_calendar.py
│   │   └── test_signal_combiner.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   └── fixtures/
│       ├── sample_news.json
│       └── sample_prices.csv
│
├── scripts/                          # Utility scripts
│   ├── seed_database.py              # Initial data seeding
│   ├── run_pipeline.py               # Manual pipeline trigger
│   ├── generate_experiment.py        # Weekly experiment script
│   └── export_research.py            # Export research data
│
└── docs/                             # Documentation
    ├── architecture.md
    ├── api_reference.md
    ├── deployment.md
    └── research_paper.md
```

---

## 3. Data Flow

### 3.1 Daily Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DAILY PIPELINE (6:00 AM EST)                             │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: INGEST (6:00 - 6:15 AM)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Alpha Vantage│  │ Yahoo Finance│  │ Reddit PRAW  │  │ Fear & Greed │    │
│  │ News API     │  │ Prices       │  │ r/stocks     │  │ Scraper      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         ▼                 ▼                 ▼                 ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         S3: raw/{source}/YYYY/MM/DD/                │   │
│  │  news_2026-01-02.json │ prices_2026-01-02.csv │ reddit_2026-01-02.json │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
STEP 2: PROCESS (6:15 - 6:20 AM)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        TEXT PROCESSING PIPELINE                       │   │
│  │                                                                       │   │
│  │  Raw Text ──► Clean ──► Extract Tickers ──► Deduplicate ──► Validate │   │
│  │                                                                       │   │
│  │  • Remove HTML tags          • Match against S&P 500 list            │   │
│  │  • Normalize whitespace      • Fuzzy match company names             │   │
│  │  • Handle encoding           • Remove near-duplicates (>90% similar) │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                       │                                      │
│                                       ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    S3: processed/YYYY/MM/DD/                         │   │
│  │  cleaned_news.json │ cleaned_reddit.json │ ticker_mappings.json     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
STEP 3: SCORE (6:20 - 6:25 AM)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─────────────────────────┐     ┌─────────────────────────────────────┐   │
│  │     NLP SENTIMENT       │     │      CALENDAR PATTERNS              │   │
│  │  ─────────────────────  │     │  ─────────────────────────────────  │   │
│  │  For each article:      │     │  For each stock:                    │   │
│  │  1. FinBERT inference   │     │  1. Get 18-month price history      │   │
│  │  2. Score: -1 to +1     │     │  2. Calculate monthly avg returns   │   │
│  │  3. Confidence: 0 to 1  │     │  3. Calculate win rate per month    │   │
│  │                         │     │  4. Get earnings proximity          │   │
│  │  Aggregate per stock:   │     │  5. Score: -1 to +1                 │   │
│  │  - Weighted avg by      │     │                                     │   │
│  │    recency & source     │     │                                     │   │
│  └────────────┬────────────┘     └──────────────────┬──────────────────┘   │
│               │                                      │                      │
│               └──────────────────┬───────────────────┘                      │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SIGNAL COMBINATION                              │   │
│  │  ───────────────────────────────────────────────────────────────    │   │
│  │  combined_score = (nlp_weight * nlp_score) + (cal_weight * cal_score)│   │
│  │  Default: nlp_weight = 0.6, cal_weight = 0.4                         │   │
│  │                                                                      │   │
│  │  Signal Classification:                                              │   │
│  │  • Strong Buy: combined > 0.70                                       │   │
│  │  • Buy: 0.55 < combined ≤ 0.70                                       │   │
│  │  • Hold: 0.45 ≤ combined ≤ 0.55                                      │   │
│  │  • Avoid: combined < 0.45                                            │   │
│  │                                                                      │   │
│  │  Conflict Detection:                                                 │   │
│  │  • Flag if |nlp_score - cal_score| > 0.30                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
STEP 4: STORE (6:25 - 6:30 AM)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         RDS POSTGRESQL                               │   │
│  │  ───────────────────────────────────────────────────────────────    │   │
│  │                                                                      │   │
│  │  INSERT INTO fact_sentiment (                                        │   │
│  │    stock_id, date_id, nlp_score, nlp_score_prev, nlp_momentum,      │   │
│  │    calendar_score, combined_score, signal, confidence,               │   │
│  │    article_count, reddit_count, news_sentiment, reddit_sentiment,   │   │
│  │    topics, conflict_flag, created_at                                │   │
│  │  )                                                                   │   │
│  │                                                                      │   │
│  │  UPDATE dim_fear_greed SET ...                                       │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Weekly Experiment Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEEKLY EXPERIMENT (Monday 6:30 AM)                        │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: GENERATE PICKS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  SEN2NAL PICKS                         LLM PICKS                            │
│  ─────────────                         ─────────                            │
│  SELECT ticker, combined_score         Call ChatGPT API:                    │
│  FROM fact_sentiment                   "Select 3 S&P 500 stocks..."         │
│  WHERE date = TODAY                                                         │
│    AND combined_score > 0.60           Call Gemini API:                     │
│  ORDER BY combined_score DESC          "Select 3 S&P 500 stocks..."         │
│  LIMIT 3                                                                    │
│                                        Call Grok API:                       │
│                                        "Select 3 S&P 500 stocks..."         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
STEP 2: RECORD ENTRIES (Monday 9:30 AM - Market Open)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  INSERT INTO fact_experiment (                                              │
│    week_number, year, method,                                               │
│    stock_1_ticker, stock_1_entry,                                           │
│    stock_2_ticker, stock_2_entry,                                           │
│    stock_3_ticker, stock_3_entry,                                           │
│    llm_prompt, llm_response                                                 │
│  )                                                                          │
│  VALUES                                                                      │
│    (6, 2026, 'SEN2NAL', 'AAPL', 178.52, 'MSFT', 412.30, 'JPM', 195.80, ...),│
│    (6, 2026, 'CHATGPT', 'NVDA', 875.20, 'AAPL', 178.52, 'GOOGL', 142.10,...),│
│    ...                                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 3: RECORD EXITS (Friday 4:00 PM - Market Close)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  UPDATE fact_experiment                                                      │
│  SET                                                                         │
│    stock_1_exit = [Friday close price],                                     │
│    stock_2_exit = [Friday close price],                                     │
│    stock_3_exit = [Friday close price],                                     │
│    weekly_return = AVG((exit - entry) / entry * 100)                        │
│  WHERE week_number = 6 AND year = 2026                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 4: DETERMINE WINNER
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  UPDATE fact_experiment                                                      │
│  SET is_winner = TRUE                                                        │
│  WHERE week_number = 6                                                       │
│    AND year = 2026                                                           │
│    AND weekly_return = (                                                     │
│      SELECT MAX(weekly_return)                                               │
│      FROM fact_experiment                                                    │
│      WHERE week_number = 6 AND year = 2026                                   │
│    )                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Algorithms

### 4.1 FinBERT Sentiment Scoring

```python
# src/sentiment/finbert_scorer.py

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

class FinBERTScorer:
    """
    Sentiment scoring using ProsusAI/finbert model.
    
    Output: Score from -1 (very negative) to +1 (very positive)
    """
    
    def __init__(self):
        self.model_name = "ProsusAI/finbert"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.eval()
        
        # Label mapping: 0=positive, 1=negative, 2=neutral
        self.label_map = {0: 1.0, 1: -1.0, 2: 0.0}
    
    def score_text(self, text: str) -> dict:
        """
        Score a single text.
        
        Returns:
            {
                "score": float (-1 to 1),
                "confidence": float (0 to 1),
                "label": str (positive/negative/neutral)
            }
        """
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Get predicted class and confidence
        confidence, predicted = torch.max(probs, dim=-1)
        
        # Calculate weighted score
        # Score = P(positive)*1 + P(neutral)*0 + P(negative)*(-1)
        score = probs[0][0].item() - probs[0][1].item()
        
        labels = ["positive", "negative", "neutral"]
        
        return {
            "score": round(score, 4),
            "confidence": round(confidence.item(), 4),
            "label": labels[predicted.item()]
        }
    
    def score_batch(self, texts: list[str]) -> list[dict]:
        """Score multiple texts efficiently."""
        results = []
        
        # Process in batches of 16
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            for j in range(len(batch)):
                score = probs[j][0].item() - probs[j][1].item()
                confidence = torch.max(probs[j]).item()
                predicted = torch.argmax(probs[j]).item()
                
                results.append({
                    "score": round(score, 4),
                    "confidence": round(confidence, 4),
                    "label": ["positive", "negative", "neutral"][predicted]
                })
        
        return results
```

### 4.2 Calendar Pattern Calculator

```python
# src/calendar/seasonal_patterns.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class CalendarPatternCalculator:
    """
    Calculate calendar-based seasonal patterns from historical price data.
    
    Patterns calculated:
    - Monthly average returns (18-month lookback)
    - Monthly win rate (% of months with positive returns)
    - Day of week effect (optional)
    """
    
    def __init__(self, lookback_months: int = 18):
        self.lookback_months = lookback_months
    
    def calculate_monthly_patterns(
        self, 
        price_history: pd.DataFrame
    ) -> dict:
        """
        Calculate monthly return patterns.
        
        Args:
            price_history: DataFrame with columns [date, adj_close]
        
        Returns:
            {
                "current_month": {
                    "avg_return": float,
                    "win_rate": float,
                    "sample_count": int
                },
                "historical": {1: {...}, 2: {...}, ...}
            }
        """
        df = price_history.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate monthly returns
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        
        # Get monthly OHLC
        monthly = df.groupby(['year', 'month']).agg({
            'adj_close': ['first', 'last']
        }).reset_index()
        monthly.columns = ['year', 'month', 'open', 'close']
        monthly['return'] = (monthly['close'] - monthly['open']) / monthly['open']
        
        # Filter to lookback period
        cutoff_date = datetime.now() - timedelta(days=self.lookback_months * 30)
        monthly = monthly[
            pd.to_datetime(monthly['year'].astype(str) + '-' + monthly['month'].astype(str) + '-01') 
            >= cutoff_date
        ]
        
        # Calculate patterns per month
        current_month = datetime.now().month
        patterns = {}
        
        for month in range(1, 13):
            month_data = monthly[monthly['month'] == month]
            
            if len(month_data) > 0:
                patterns[month] = {
                    "avg_return": round(month_data['return'].mean() * 100, 2),
                    "win_rate": round((month_data['return'] > 0).mean(), 2),
                    "sample_count": len(month_data)
                }
            else:
                patterns[month] = {
                    "avg_return": 0.0,
                    "win_rate": 0.5,
                    "sample_count": 0
                }
        
        return {
            "current_month": patterns.get(current_month, {}),
            "historical": patterns
        }
    
    def calculate_calendar_score(
        self, 
        patterns: dict,
        earnings_days_away: int = None
    ) -> float:
        """
        Convert patterns to a score from -1 to 1.
        
        Factors:
        - Monthly average return (normalized)
        - Win rate deviation from 50%
        - Earnings proximity boost
        """
        current = patterns.get("current_month", {})
        
        # Base score from average return (cap at ±10% = ±1.0)
        avg_return = current.get("avg_return", 0)
        return_score = np.clip(avg_return / 10, -1, 1)
        
        # Win rate factor (0.5 = neutral, 1.0 = max boost)
        win_rate = current.get("win_rate", 0.5)
        win_factor = (win_rate - 0.5) * 2  # -1 to 1
        
        # Combine
        score = 0.7 * return_score + 0.3 * win_factor
        
        # Earnings proximity adjustment (optional)
        if earnings_days_away is not None:
            if earnings_days_away <= 7:
                # Close to earnings - increase uncertainty
                score *= 0.8
        
        return round(np.clip(score, -1, 1), 4)
```

### 4.3 Signal Combiner with Conflict Detection

```python
# src/features/signal_combiner.py

from dataclasses import dataclass
from enum import Enum

class Signal(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    AVOID = "AVOID"

@dataclass
class CombinedSignal:
    combined_score: float
    signal: Signal
    nlp_score: float
    calendar_score: float
    nlp_weight: float
    calendar_weight: float
    conflict_flag: bool
    conflict_reason: str | None
    confidence: float

class SignalCombiner:
    """
    Combines NLP sentiment and calendar patterns into a unified signal.
    """
    
    def __init__(
        self, 
        nlp_weight: float = 0.6,
        calendar_weight: float = 0.4,
        conflict_threshold: float = 0.30
    ):
        self.nlp_weight = nlp_weight
        self.calendar_weight = calendar_weight
        self.conflict_threshold = conflict_threshold
        
        # Signal thresholds
        self.thresholds = {
            Signal.STRONG_BUY: 0.70,
            Signal.BUY: 0.55,
            Signal.HOLD: 0.45,
            # Below HOLD = AVOID
        }
    
    def combine(
        self,
        nlp_score: float,
        calendar_score: float,
        nlp_confidence: float = 1.0
    ) -> CombinedSignal:
        """
        Combine scores into unified signal.
        
        Args:
            nlp_score: -1 to 1 (from FinBERT)
            calendar_score: -1 to 1 (from calendar patterns)
            nlp_confidence: 0 to 1 (FinBERT confidence)
        
        Returns:
            CombinedSignal with all details
        """
        # Normalize scores from [-1, 1] to [0, 1] for easier thresholding
        nlp_norm = (nlp_score + 1) / 2
        cal_norm = (calendar_score + 1) / 2
        
        # Weighted combination
        combined = (
            self.nlp_weight * nlp_norm + 
            self.calendar_weight * cal_norm
        )
        
        # Detect conflict
        conflict_flag = abs(nlp_norm - cal_norm) > self.conflict_threshold
        conflict_reason = None
        
        if conflict_flag:
            nlp_label = "Bullish" if nlp_norm > 0.55 else ("Bearish" if nlp_norm < 0.45 else "Neutral")
            cal_label = "Bullish" if cal_norm > 0.55 else ("Bearish" if cal_norm < 0.45 else "Neutral")
            conflict_reason = f"NLP: {nlp_label} ({nlp_norm:.2f}) vs Calendar: {cal_label} ({cal_norm:.2f})"
        
        # Determine signal
        if combined >= self.thresholds[Signal.STRONG_BUY]:
            signal = Signal.STRONG_BUY
        elif combined >= self.thresholds[Signal.BUY]:
            signal = Signal.BUY
        elif combined >= self.thresholds[Signal.HOLD]:
            signal = Signal.HOLD
        else:
            signal = Signal.AVOID
        
        # Confidence calculation
        # Lower confidence if:
        # - NLP confidence is low
        # - There's a conflict
        # - Score is near threshold boundaries
        base_confidence = nlp_confidence
        
        if conflict_flag:
            base_confidence *= 0.7
        
        # Reduce confidence near boundaries
        boundary_distances = [
            abs(combined - t) for t in self.thresholds.values()
        ]
        min_boundary_dist = min(boundary_distances)
        if min_boundary_dist < 0.05:
            base_confidence *= 0.8
        
        return CombinedSignal(
            combined_score=round(combined, 4),
            signal=signal,
            nlp_score=nlp_score,
            calendar_score=calendar_score,
            nlp_weight=self.nlp_weight,
            calendar_weight=self.calendar_weight,
            conflict_flag=conflict_flag,
            conflict_reason=conflict_reason,
            confidence=round(base_confidence, 4)
        )
```

---

## 5. API Implementation

### 5.1 FastAPI Application Structure

```python
# src/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routers import health, stocks, sectors, market, experiment
from src.database.connection import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Sen2Nal API...")
    yield
    # Shutdown
    print("Shutting down Sen2Nal API...")

app = FastAPI(
    title="Sen2Nal API",
    description="Stock Sentiment + Calendar Signal Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(stocks.router, prefix="/api/v1", tags=["Stocks"])
app.include_router(sectors.router, prefix="/api/v1", tags=["Sectors"])
app.include_router(market.router, prefix="/api/v1", tags=["Market"])
app.include_router(experiment.router, prefix="/api/v1", tags=["Experiment"])
```

### 5.2 Pydantic Schemas

```python
# src/api/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class SignalType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    AVOID = "AVOID"

class FearGreedClassification(str, Enum):
    EXTREME_FEAR = "Extreme Fear"
    FEAR = "Fear"
    NEUTRAL = "Neutral"
    GREED = "Greed"
    EXTREME_GREED = "Extreme Greed"

# Response Models

class FearGreedResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    classification: FearGreedClassification
    change: int
    updated_at: datetime

class StockSummary(BaseModel):
    rank: int
    ticker: str
    company_name: str
    nlp_score: float = Field(..., ge=-1, le=1)
    nlp_momentum: float
    calendar_score: float = Field(..., ge=-1, le=1)
    combined_score: float = Field(..., ge=0, le=1)
    signal: SignalType
    conflict_flag: bool

class Top10Response(BaseModel):
    updated_at: datetime
    fear_greed: FearGreedResponse
    stocks: list[StockSummary]

class PriceInfo(BaseModel):
    current: float
    change: float
    change_percent: float

class NLPBreakdown(BaseModel):
    news_score: float
    news_count: int
    reddit_score: float
    reddit_count: int
    topics: list[str]

class CalendarBreakdown(BaseModel):
    month_avg_return: float
    month_win_rate: float
    days_to_earnings: int | None
    pattern_description: str

class FeatureContribution(BaseModel):
    feature: str
    contribution: float

class Explainability(BaseModel):
    top_features: list[FeatureContribution]

class ConflictInfo(BaseModel):
    nlp_signal: str
    calendar_signal: str
    reason: str
    historical_resolution: str

class SentimentInfo(BaseModel):
    nlp_score: float
    nlp_momentum: float
    nlp_trend: str
    calendar_score: float
    combined_score: float
    signal: SignalType
    confidence: float

class StockDetailResponse(BaseModel):
    ticker: str
    company_name: str
    sector: str
    price: PriceInfo
    sentiment: SentimentInfo
    nlp_breakdown: NLPBreakdown
    calendar_breakdown: CalendarBreakdown
    explainability: Explainability
    conflict: ConflictInfo | None
    updated_at: datetime

class SectorSentiment(BaseModel):
    sector: str
    avg_sentiment: float
    stock_count: int
    bullish_count: int
    bearish_count: int

class SectorsResponse(BaseModel):
    updated_at: datetime
    sectors: list[SectorSentiment]

class ExperimentPick(BaseModel):
    ticker: str
    score: float | None  # None for LLM picks
    reasoning: str | None

class WeekResult(BaseModel):
    week: int
    year: int
    method: str
    picks: list[ExperimentPick]
    weekly_return: float | None
    is_winner: bool

class ExperimentResponse(BaseModel):
    current_week: int
    total_weeks: int
    status: str  # "LIVE" or "COMPLETE"
    this_week: dict[str, list[ExperimentPick]]
    cumulative_results: list[WeekResult]
    totals: dict[str, float]
    win_counts: dict[str, int]
```

---

## 6. AWS Infrastructure

### 6.1 CloudFormation Template (Main Stack)

```yaml
# infrastructure/cloudformation/main.yaml

AWSTemplateFormatVersion: '2010-09-09'
Description: Sen2Nal Infrastructure Stack

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, production]
  
  DBPassword:
    Type: String
    NoEcho: true
    Description: PostgreSQL master password

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: sen2nal-vpc

  # Public Subnet
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: sen2nal-public-subnet

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Route Table
  RouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  Route:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref RouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  SubnetRouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet
      RouteTableId: !Ref RouteTable

  # Security Group for EC2
  EC2SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Sen2Nal EC2
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0  # Restrict in production
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 8501
          ToPort: 8501
          CidrIp: 0.0.0.0/0

  # Security Group for RDS
  RDSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Sen2Nal RDS
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref EC2SecurityGroup

  # EC2 Instance
  EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t3.medium
      ImageId: ami-0c02fb55956c7d316  # Amazon Linux 2 (update for region)
      SubnetId: !Ref PublicSubnet
      SecurityGroupIds:
        - !Ref EC2SecurityGroup
      KeyName: sen2nal-key  # Create this key pair first
      IamInstanceProfile: !Ref EC2InstanceProfile
      Tags:
        - Key: Name
          Value: sen2nal-server
      UserData:
        Fn::Base64: |
          #!/bin/bash
          yum update -y
          yum install -y python3.11 python3.11-pip git
          pip3.11 install poetry

  # EC2 IAM Role (for S3 access)
  EC2Role:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonS3FullAccess

  EC2InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref EC2Role

  # S3 Bucket
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'sen2nal-data-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldRawData
            Status: Enabled
            Prefix: raw/
            ExpirationInDays: 90

  # RDS Subnet Group
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for Sen2Nal RDS
      SubnetIds:
        - !Ref PublicSubnet
        - !Ref PublicSubnet2  # Need second subnet in different AZ

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      MapPublicIpOnLaunch: true
      AvailabilityZone: !Select [1, !GetAZs '']

  # RDS Instance
  RDSInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: sen2nal-db
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: '15'
      MasterUsername: sen2nal_admin
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: 20
      StorageType: gp2
      VPCSecurityGroups:
        - !Ref RDSSecurityGroup
      DBSubnetGroupName: !Ref DBSubnetGroup
      PubliclyAccessible: false
      BackupRetentionPeriod: 7

Outputs:
  EC2PublicIP:
    Description: Public IP of EC2 instance
    Value: !GetAtt EC2Instance.PublicIp
  
  RDSEndpoint:
    Description: RDS endpoint
    Value: !GetAtt RDSInstance.Endpoint.Address
  
  S3BucketName:
    Description: S3 bucket name
    Value: !Ref DataBucket
```

---

## 7. Deployment Guide

### 7.1 Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/sen2nal.git
cd sen2nal

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install poetry
poetry install

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database credentials

# 5. Start local PostgreSQL (Docker)
docker-compose up -d postgres

# 6. Run database migrations
alembic upgrade head

# 7. Seed initial data
python scripts/seed_database.py

# 8. Start API server
uvicorn src.api.main:app --reload --port 8000

# 9. Start Streamlit (new terminal)
streamlit run src/dashboard/app.py --server.port 8501
```

### 7.2 Production Deployment

```bash
# On EC2 instance

# 1. Clone repository
git clone https://github.com/yourusername/sen2nal.git
cd sen2nal

# 2. Install dependencies
pip install poetry
poetry install --no-dev

# 3. Set up environment variables
export DATABASE_URL="postgresql://user:pass@rds-endpoint:5432/sen2nal"
export S3_BUCKET="sen2nal-data-123456789"
export ALPHA_VANTAGE_KEY="your_key"
# ... other keys

# 4. Run migrations
alembic upgrade head

# 5. Seed data
python scripts/seed_database.py

# 6. Start services with systemd
sudo cp infrastructure/systemd/sen2nal-api.service /etc/systemd/system/
sudo cp infrastructure/systemd/sen2nal-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sen2nal-api sen2nal-dashboard
sudo systemctl start sen2nal-api sen2nal-dashboard

# 7. Set up cron for daily pipeline
crontab -e
# Add: 0 6 * * * cd /home/ec2-user/sen2nal && /usr/bin/python scripts/run_pipeline.py
```

---

## 8. Monitoring & Logging

### 8.1 Logging Configuration

```python
# src/config.py

import logging
import sys
from datetime import datetime

def setup_logging():
    """Configure logging for the application."""
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler (daily rotation)
    file_handler = logging.FileHandler(
        f"logs/sen2nal_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger
```

### 8.2 Pipeline Monitoring

```python
# src/ingestion/scheduler.py

from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PipelineMetrics:
    start_time: datetime
    end_time: datetime | None = None
    articles_ingested: int = 0
    reddit_posts_ingested: int = 0
    stocks_scored: int = 0
    errors: list[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    @property
    def success(self) -> bool:
        return len(self.errors) == 0 and self.stocks_scored > 0

def run_daily_pipeline() -> PipelineMetrics:
    """Execute the daily data pipeline with monitoring."""
    
    metrics = PipelineMetrics(start_time=datetime.now())
    
    try:
        # Step 1: Ingest
        logger.info("Starting data ingestion...")
        articles = ingest_news()
        metrics.articles_ingested = len(articles)
        
        posts = ingest_reddit()
        metrics.reddit_posts_ingested = len(posts)
        
        # Step 2: Process
        logger.info("Processing text data...")
        processed = process_articles(articles + posts)
        
        # Step 3: Score
        logger.info("Scoring sentiment...")
        scores = score_sentiment(processed)
        metrics.stocks_scored = len(scores)
        
        # Step 4: Store
        logger.info("Storing results...")
        store_scores(scores)
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        metrics.errors.append(str(e))
    
    finally:
        metrics.end_time = datetime.now()
        logger.info(f"Pipeline completed in {metrics.duration_seconds:.2f}s")
        logger.info(f"Metrics: {metrics}")
        
        # Store metrics for monitoring dashboard
        store_pipeline_metrics(metrics)
    
    return metrics
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/unit/test_signal_combiner.py

import pytest
from src.features.signal_combiner import SignalCombiner, Signal

class TestSignalCombiner:
    
    def setup_method(self):
        self.combiner = SignalCombiner(
            nlp_weight=0.6,
            calendar_weight=0.4,
            conflict_threshold=0.30
        )
    
    def test_strong_buy_signal(self):
        """Both signals positive should give STRONG_BUY."""
        result = self.combiner.combine(
            nlp_score=0.8,      # Very positive
            calendar_score=0.7  # Positive
        )
        assert result.signal == Signal.STRONG_BUY
        assert result.combined_score > 0.70
    
    def test_avoid_signal(self):
        """Both signals negative should give AVOID."""
        result = self.combiner.combine(
            nlp_score=-0.6,
            calendar_score=-0.4
        )
        assert result.signal == Signal.AVOID
        assert result.combined_score < 0.45
    
    def test_conflict_detection(self):
        """Opposing signals should trigger conflict flag."""
        result = self.combiner.combine(
            nlp_score=0.7,       # Bullish
            calendar_score=-0.5  # Bearish
        )
        assert result.conflict_flag == True
        assert result.conflict_reason is not None
        assert "vs" in result.conflict_reason
    
    def test_no_conflict_when_aligned(self):
        """Similar signals should not trigger conflict."""
        result = self.combiner.combine(
            nlp_score=0.5,
            calendar_score=0.4
        )
        assert result.conflict_flag == False
    
    def test_confidence_reduced_on_conflict(self):
        """Confidence should be lower when signals conflict."""
        no_conflict = self.combiner.combine(0.5, 0.5)
        with_conflict = self.combiner.combine(0.8, -0.5)
        
        assert with_conflict.confidence < no_conflict.confidence
```

### 9.2 Integration Tests

```python
# tests/integration/test_api.py

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestStocksAPI:
    
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_top10_returns_stocks(self):
        response = client.get("/api/v1/stocks/top10")
        assert response.status_code == 200
        
        data = response.json()
        assert "stocks" in data
        assert len(data["stocks"]) == 10
        assert "fear_greed" in data
    
    def test_stock_detail_valid_ticker(self):
        response = client.get("/api/v1/stocks/AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "sentiment" in data
        assert "nlp_breakdown" in data
        assert "calendar_breakdown" in data
    
    def test_stock_detail_invalid_ticker(self):
        response = client.get("/api/v1/stocks/INVALID123")
        assert response.status_code == 404
    
    def test_search_stocks(self):
        response = client.get("/api/v1/stocks/search?q=apple")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        assert any(s["ticker"] == "AAPL" for s in data)
```

---

## 10. Performance Considerations

### 10.1 Optimization Strategies

| Area | Strategy | Implementation |
|------|----------|----------------|
| **FinBERT Inference** | Batch processing | Process 16 texts at a time |
| **Database Queries** | Indexing | Index on (stock_id, date_id) |
| **API Response** | Caching | Redis cache for top10, 5-min TTL |
| **S3 Access** | Compression | gzip raw JSON files |
| **Dashboard** | Lazy loading | Load detailed data on click |

### 10.2 Database Indexes

```sql
-- Essential indexes for performance
CREATE INDEX idx_fact_sentiment_stock_date 
ON fact_sentiment(stock_id, date_id DESC);

CREATE INDEX idx_fact_sentiment_date 
ON fact_sentiment(date_id DESC);

CREATE INDEX idx_fact_prices_stock_date 
ON fact_prices(stock_id, date_id DESC);

CREATE INDEX idx_dim_stocks_ticker 
ON dim_stocks(ticker);

CREATE INDEX idx_fact_experiment_week 
ON fact_experiment(year, week_number);
```

---

This technical architecture document provides the complete blueprint for implementing Sen2Nal. All code samples are production-ready patterns that can be directly used or adapted during development.
