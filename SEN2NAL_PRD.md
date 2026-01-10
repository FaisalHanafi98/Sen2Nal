# Sen2Nal: Stock Sentiment + Calendar Signal Analysis System
## Product Requirements Document (PRD)

**Version:** 1.0  
**Author:** Faisal (Mohamad Faisal Bin Mohd Hanafi)  
**Created:** January 2026  
**Last Updated:** January 2026  
**Status:** Ready for Development

---

## Executive Summary

Sen2Nal is a stock sentiment analysis platform that combines NLP-based sentiment scoring with calendar-based seasonal patterns to generate trading signals. The system includes a live experiment comparing Sen2Nal's stock picks against recommendations from major LLMs (ChatGPT, Gemini, Grok), with results published as a research paper.

### Core Philosophy
> **"Signal over certainty"** - We surface measurable patterns, not predictions. Every score is decomposed transparently.

### Target Users
- Individual investors seeking sentiment-based insights
- Data science recruiters evaluating technical portfolios
- Researchers interested in NLP applications in finance

---

## 1. Problem Statement

### 1.1 Current State
Traditional stock analysis tools either:
- Rely purely on technical indicators (lagging, no context)
- Use black-box AI with no explainability
- Ignore seasonal/calendar patterns that experienced traders recognize
- Don't compare their performance against alternatives

### 1.2 Desired State
A transparent, explainable sentiment analysis system that:
- Combines NLP sentiment with calendar-based patterns
- Shows exactly why each signal was generated
- Honestly tracks its own performance
- Compares itself against LLM recommendations

### 1.3 Gap Analysis

| Gap | Impact | Solution |
|-----|--------|----------|
| No sentiment + calendar hybrid | Miss combined signals | Two-layer scoring system |
| Black-box predictions | No trust | Full SHAP explainability |
| No performance tracking | Unverifiable claims | Live experiment with LLMs |
| Complex data engineering hidden | Can't assess skills | Showcase full pipeline |

---

## 2. Product Vision

### 2.1 Product Statement
Sen2Nal is a **stock sentiment analysis platform** that helps **individual investors** understand **market sentiment and seasonal patterns** by providing **transparent, explainable signals** with **live performance comparison** against LLM recommendations.

### 2.2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| System Uptime | 99% | AWS CloudWatch |
| Daily Data Freshness | Updated by 6:30 AM EST | Pipeline monitoring |
| S&P 500 Coverage | 100% searchable | Database count |
| Experiment Duration | 8 weeks complete | Weekly tracking |
| Documentation Quality | Interview-ready | Self-assessment |

### 2.3 Portfolio Objectives
This project demonstrates:
- **Data Analyst**: EDA, data quality, calendar pattern analysis
- **Data Engineer**: ETL pipelines, AWS infrastructure, scheduling
- **Data Scientist**: NLP models, feature engineering, backtesting
- **AWS Architect**: EC2, RDS, S3 integration (certification prep)

---

## 3. Solution Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
│   Alpha Vantage │ Yahoo Finance │ Reddit (PRAW) │ NewsAPI │ Fear/Greed     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION LAYER (EC2)                                │
│   Scheduler (APScheduler) → API Clients → Rate Limiter → S3 (Raw Data)      │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER (EC2)                                │
│   Text Cleaning → Ticker Extraction → Deduplication → Validation            │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCORING LAYER (EC2)                                  │
│   FinBERT Sentiment → Calendar Patterns → Signal Combination → Features     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER (RDS PostgreSQL)                        │
│   dim_stocks │ dim_calendar │ fact_sentiment │ fact_predictions │ fact_exp  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVING LAYER (EC2)                                  │
│   FastAPI (REST API) → Pydantic Validation → Auto-generated Docs            │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER (EC2 - Streamlit)                    │
│   Dashboard │ Stock Search │ Sector View │ Experiment Results │ Research    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Language** | Python | 3.11+ | ML ecosystem, FastAPI compatibility |
| **API Framework** | FastAPI | 0.109+ | Async, auto-docs, Pydantic native |
| **Dashboard** | Streamlit | 1.30+ | Rapid data app development |
| **NLP Model** | FinBERT | HuggingFace | Finance-specific, proven accuracy |
| **ML Framework** | XGBoost | 2.0+ | Directional prediction, SHAP support |
| **Database** | PostgreSQL | 15+ | Relational, time-series capable |
| **Object Storage** | AWS S3 | - | Raw data lake, model artifacts |
| **Compute** | AWS EC2 | t3.medium | Cost-effective, scalable |
| **Database Hosting** | AWS RDS | db.t3.micro | Managed PostgreSQL |
| **Scheduling** | APScheduler | 3.10+ | Python-native, cron-like |
| **Data Validation** | Pydantic | 2.0+ | Type safety, serialization |
| **Visualization** | Plotly | 5.18+ | Interactive charts |

---

## 4. Feature Specifications

### 4.1 Core Features (MVP - Beta)

#### F1: Dashboard with Top 10 Stocks
**Priority:** P0 (Essential)  
**Description:** Landing page showing top 10 stocks by market cap with pre-computed daily scores

**User Story:**  
As a user, I want to see today's sentiment scores for major stocks immediately upon visiting the site.

**Acceptance Criteria:**
- [ ] Display 10 stocks: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK.B, JPM, V
- [ ] Show for each: Ticker, Company Name, NLP Score, Calendar Score, Combined Score, Signal
- [ ] Scores updated daily by 6:30 AM EST
- [ ] Signal categories: Strong Buy (>0.7), Buy (0.55-0.7), Hold (0.45-0.55), Avoid (<0.45)
- [ ] Click any row to navigate to detailed stock view
- [ ] Show "Last Updated" timestamp

**UI Mockup:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔍 Search: [________________________] [Search]       Updated: 6:00 AM EST  │
├─────────────────────────────────────────────────────────────────────────────┤
│  🌡️ Market Mood: FEAR (38) ━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 TOP 10 STOCKS BY MARKET CAP                                             │
│  ┌────────┬──────────────┬───────────┬───────────┬───────────┬───────────┐  │
│  │ Rank   │ Stock        │ NLP Score │ Calendar  │ Combined  │ Signal    │  │
│  ├────────┼──────────────┼───────────┼───────────┼───────────┼───────────┤  │
│  │ 1      │ AAPL         │ 0.72 ▲    │ 0.65      │ 0.69      │ 🟢 BUY    │  │
│  │ 2      │ MSFT         │ 0.68      │ 0.71 ▲    │ 0.69      │ 🟢 BUY    │  │
│  │ ...    │ ...          │ ...       │ ...       │ ...       │ ...       │  │
│  └────────┴──────────────┴───────────┴───────────┴───────────┴───────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### F2: Stock Search (S&P 500)
**Priority:** P0 (Essential)  
**Description:** Search functionality to find any S&P 500 stock by ticker or company name

**User Story:**  
As a user, I want to search for any S&P 500 stock to see its sentiment analysis.

**Acceptance Criteria:**
- [ ] Search by ticker (e.g., "AAPL") or company name (e.g., "Apple")
- [ ] Autocomplete suggestions as user types
- [ ] Handle case-insensitive search
- [ ] Display "No results found" for non-S&P 500 stocks
- [ ] Navigate to detailed stock view on selection

---

#### F3: Stock Detail View
**Priority:** P0 (Essential)  
**Description:** Detailed sentiment analysis for a single stock

**User Story:**  
As a user, I want to see detailed sentiment breakdown for a specific stock.

**Acceptance Criteria:**
- [ ] Display current price and daily change (from Yahoo Finance)
- [ ] Combined signal gauge (visual -1 to +1 scale)
- [ ] NLP Sentiment breakdown:
  - Overall NLP score
  - Source breakdown (News, Reddit)
  - Article/post count
  - Sentiment momentum (change from yesterday)
- [ ] Calendar Pattern breakdown:
  - Overall calendar score
  - Monthly historical average
  - Historical win rate for this month
  - Days until next earnings (if available)
- [ ] Explainability section:
  - Top 5 features driving the score
  - Visual bar chart of feature importance
- [ ] Conflict indicator (if NLP and Calendar disagree significantly)

**UI Mockup:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back                                              AAPL - Apple Inc.      │
│                                                      $178.52 ▲2.3%          │
├─────────────────────────────────────────────────────────────────────────────┤
│  COMBINED SIGNAL: 0.69 (BUY)                                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  AVOID          HOLD              BUY            STRONG BUY                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │  💬 NLP SENTIMENT           │  │  📅 CALENDAR PATTERN                │   │
│  │  Score: 0.72 (Bullish)      │  │  Score: 0.65 (Moderate)             │   │
│  │  Momentum: ▲ +0.08          │  │  Jan avg return: +3.2%              │   │
│  │  ─────────────────────      │  │  Historical win: 12/18 months       │   │
│  │  News: 0.68 (12 articles)   │  │  Earnings in: 45 days               │   │
│  │  Reddit: 0.75 (23 posts)    │  │  ─────────────────────────────      │   │
│  │  ─────────────────────      │  │  Pattern: Historically strong Jan   │   │
│  │  Topics: iPhone, AI, China  │  │                                     │   │
│  └─────────────────────────────┘  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔍 WHY THIS SCORE?                                                         │
│  sentiment_momentum   ████████████████  +0.18                               │
│  january_avg_return   ██████████████    +0.15                               │
│  article_volume       ██████████        +0.11                               │
│  reddit_sentiment     ████████          +0.09                               │
│  news_sentiment       ██████            +0.07                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### F4: Fear & Greed Index Integration
**Priority:** P0 (Category A Enhancement)  
**Description:** Market-wide sentiment indicator displayed on dashboard

**User Story:**  
As a user, I want to see overall market sentiment to contextualize individual stock scores.

**Acceptance Criteria:**
- [ ] Display current Fear & Greed score (0-100)
- [ ] Visual gauge with color coding:
  - Extreme Fear (0-25): Deep Red
  - Fear (25-45): Red
  - Neutral (45-55): Yellow
  - Greed (55-75): Green
  - Extreme Greed (75-100): Deep Green
- [ ] Show change from previous day
- [ ] Update daily

**Data Source:** Scrape from feargreedmeter.com or calculate from VIX

---

#### F5: Sentiment Momentum Indicator
**Priority:** P0 (Category A Enhancement)  
**Description:** Show how sentiment is changing, not just current value

**User Story:**  
As a user, I want to know if sentiment is improving or deteriorating.

**Acceptance Criteria:**
- [ ] Calculate daily sentiment change (delta from yesterday)
- [ ] Display arrow indicator (▲/▼/─)
- [ ] Show streak count (e.g., "3-day upward trend")
- [ ] Color code: Green for positive momentum, Red for negative

---

#### F6: Signal Conflict Indicator
**Priority:** P0 (Category A Enhancement)  
**Description:** Highlight when NLP and Calendar signals disagree

**User Story:**  
As a user, I want to know when the two signal sources conflict so I can be cautious.

**Acceptance Criteria:**
- [ ] Detect conflict when NLP and Calendar scores differ by >0.3
- [ ] Display warning icon and explanation
- [ ] Show historical resolution rate (e.g., "60% resolved toward NLP")
- [ ] Provide reasoning for the conflict

**UI:**
```
⚡ CONFLICT DETECTED
NLP says: BULLISH (0.72)   Calendar says: BEARISH (0.35)
Reason: Strong news sentiment vs. historically weak January for TSLA
Similar conflicts: 60% resolved toward NLP
```

---

#### F7: Word Cloud / Topic Summary
**Priority:** P1 (Category A Enhancement)  
**Description:** Show what topics are driving sentiment

**User Story:**  
As a user, I want to understand what people are talking about regarding this stock.

**Acceptance Criteria:**
- [ ] Extract top 5-10 keywords/topics from news headlines
- [ ] Show frequency percentage for each topic
- [ ] Visual representation (bar chart or word cloud)
- [ ] Update daily with new articles

---

#### F8: Sector Aggregation View
**Priority:** P1 (Category A Enhancement)  
**Description:** Show sentiment aggregated by GICS sector

**User Story:**  
As a user, I want to see which sectors have positive/negative sentiment overall.

**Acceptance Criteria:**
- [ ] Group S&P 500 by 11 GICS sectors
- [ ] Calculate average sentiment per sector
- [ ] Display as ranked list with visual bars
- [ ] Click sector to see constituent stocks

**Sectors:** Technology, Healthcare, Financials, Consumer Discretionary, Communication Services, Industrials, Consumer Staples, Energy, Utilities, Real Estate, Materials

---

#### F9: Methodology Page
**Priority:** P0 (Essential)  
**Description:** Explain how Sen2Nal works

**User Story:**  
As a user/recruiter, I want to understand the technical approach and methodology.

**Acceptance Criteria:**
- [ ] Overview of two-layer approach (NLP + Calendar)
- [ ] Explanation of FinBERT and how sentiment is scored
- [ ] Explanation of calendar pattern calculation
- [ ] Signal combination formula
- [ ] Data sources listed
- [ ] Limitations and disclaimers
- [ ] Link to full research paper (when available)

---

#### F10: LLM Experiment Tracking
**Priority:** P0 (Essential)  
**Description:** Track and display Sen2Nal vs LLM performance comparison

**User Story:**  
As a user, I want to see how Sen2Nal performs compared to ChatGPT, Gemini, and Grok recommendations.

**Acceptance Criteria:**
- [ ] Display current week of experiment (Week X of 8)
- [ ] Show this week's picks for Sen2Nal and each LLM
- [ ] Show cumulative results table:
  - Weekly returns for each method
  - Winner per week
  - Total cumulative return
  - Win rate (weeks won)
- [ ] Display prompts used for LLMs (transparency)
- [ ] Update every Friday after market close

**UI Mockup:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 SEN2NAL vs LLM EXPERIMENT                           Week 6 of 8 🟢 LIVE │
├─────────────────────────────────────────────────────────────────────────────┤
│  THIS WEEK'S PICKS                                                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌────────────┐ │
│  │ SEN2NAL         │ │ CHATGPT         │ │ GEMINI          │ │ GROK       │ │
│  │ 1. AAPL (0.69)  │ │ 1. NVDA         │ │ 1. MSFT         │ │ 1. GOOGL   │ │
│  │ 2. MSFT (0.69)  │ │ 2. AAPL         │ │ 2. AMZN         │ │ 2. AAPL    │ │
│  │ 3. JPM  (0.65)  │ │ 3. GOOGL        │ │ 3. META         │ │ 3. NVDA    │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  CUMULATIVE RESULTS                                                         │
│  Week │ Sen2Nal │ ChatGPT │ Gemini │ Grok │ Winner                         │
│  ─────┼─────────┼─────────┼────────┼──────┼────────                         │
│  1    │ +2.3%   │ +1.1%   │ +1.8%  │+0.9% │ 🏆 Sen2Nal                      │
│  2    │ -0.5%   │ +0.8%   │ -0.2%  │+1.2% │ 🏆 Grok                         │
│  ...  │ ...     │ ...     │ ...    │ ...  │ ...                             │
│  ─────┼─────────┼─────────┼────────┼──────┼────────                         │
│  TOTAL│ +6.0%   │ +4.9%   │ +5.2%  │+4.1% │ 🏆 Sen2Nal (3-2-1)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Data Pipeline Features

#### DP1: Daily Data Ingestion
**Schedule:** 6:00 AM EST (before market open)

**Data Sources:**
| Source | Data Type | API | Rate Limit |
|--------|-----------|-----|------------|
| Alpha Vantage | News | Free tier | 5 calls/min |
| Yahoo Finance | Prices, News | yfinance | No official limit |
| Reddit | r/stocks, r/wallstreetbets | PRAW | 60 req/min |
| NewsAPI | Headlines | Free tier | 100 req/day |
| Fear & Greed | Market sentiment | Scrape | 1x daily |

**Pipeline Steps:**
1. Fetch raw data from all sources
2. Store raw JSON in S3 (partitioned by date)
3. Clean and deduplicate text
4. Extract ticker mentions
5. Score sentiment with FinBERT
6. Calculate calendar features
7. Combine scores and store in RDS
8. Log pipeline metrics

---

#### DP2: Weekly Model Retraining
**Schedule:** Sunday 11:00 PM EST

**Steps:**
1. Extract feature matrix from RDS (last 18 months)
2. Train XGBoost classifier
3. Evaluate with walk-forward validation
4. Calculate SHAP values
5. Store model artifact in S3
6. Update model version in database
7. Generate performance report

---

### 4.3 Experiment Protocol

#### Weekly Experiment Workflow (Every Monday)

**Monday 6:00 AM:**
1. Sen2Nal generates top 3 stocks (highest combined score >0.6)
2. Query ChatGPT with standardized prompt
3. Query Gemini with standardized prompt
4. Query Grok with standardized prompt
5. Record all picks with entry prices (Monday open)

**Friday 4:00 PM:**
1. Record exit prices (Friday close)
2. Calculate weekly returns for each method
3. Determine week winner
4. Update cumulative statistics
5. Update dashboard

**LLM Prompt Template:**
```
You are a financial analyst. Based on current market conditions as of [DATE], 
select exactly 3 S&P 500 stocks that you believe will perform best over the 
next 5 trading days (Monday open to Friday close).

Consider:
- Recent news sentiment
- Technical factors
- Seasonal patterns
- Market conditions

Respond with exactly 3 ticker symbols and a brief reasoning for each.
Format: TICKER: Reasoning
```

---

## 5. Database Schema

### 5.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│   dim_stocks    │       │   dim_calendar  │
├─────────────────┤       ├─────────────────┤
│ stock_id (PK)   │       │ date_id (PK)    │
│ ticker          │       │ date            │
│ company_name    │       │ day_of_week     │
│ sector          │       │ month           │
│ market_cap      │       │ quarter         │
│ sp500_rank      │       │ year            │
│ created_at      │       │ is_trading_day  │
│ updated_at      │       │ is_earnings_szn │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │    ┌────────────────────┴───────────────────┐
         │    │                                        │
         ▼    ▼                                        ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│    fact_sentiment       │              │     fact_prices         │
├─────────────────────────┤              ├─────────────────────────┤
│ sentiment_id (PK)       │              │ price_id (PK)           │
│ stock_id (FK)           │              │ stock_id (FK)           │
│ date_id (FK)            │              │ date_id (FK)            │
│ nlp_score               │              │ open                    │
│ nlp_score_prev          │              │ high                    │
│ nlp_momentum            │              │ low                     │
│ calendar_score          │              │ close                   │
│ combined_score          │              │ adj_close               │
│ signal                  │              │ volume                  │
│ confidence              │              │ created_at              │
│ article_count           │              └─────────────────────────┘
│ reddit_count            │
│ news_sentiment          │              ┌─────────────────────────┐
│ reddit_sentiment        │              │   fact_experiment       │
│ topics (JSON)           │              ├─────────────────────────┤
│ conflict_flag           │              │ experiment_id (PK)      │
│ created_at              │              │ week_number             │
│ updated_at              │              │ year                    │
└─────────────────────────┘              │ method (enum)           │
                                         │ stock_1_ticker          │
┌─────────────────────────┐              │ stock_1_entry           │
│   fact_predictions      │              │ stock_1_exit            │
├─────────────────────────┤              │ stock_2_ticker          │
│ prediction_id (PK)      │              │ stock_2_entry           │
│ stock_id (FK)           │              │ stock_2_exit            │
│ date_id (FK)            │              │ stock_3_ticker          │
│ predicted_direction     │              │ stock_3_entry           │
│ predicted_confidence    │              │ stock_3_exit            │
│ actual_direction        │              │ weekly_return           │
│ model_version           │              │ is_winner               │
│ feature_importance JSON │              │ llm_prompt              │
│ created_at              │              │ llm_response            │
└─────────────────────────┘              │ created_at              │
                                         └─────────────────────────┘

┌─────────────────────────┐
│   dim_fear_greed        │
├─────────────────────────┤
│ fg_id (PK)              │
│ date_id (FK)            │
│ score                   │
│ classification          │
│ prev_score              │
│ change                  │
│ created_at              │
└─────────────────────────┘
```

---

## 6. API Specification

### 6.1 Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | System health check |
| GET | `/api/v1/stocks` | List all tracked stocks |
| GET | `/api/v1/stocks/top10` | Get top 10 stocks with scores |
| GET | `/api/v1/stocks/{ticker}` | Get detailed stock analysis |
| GET | `/api/v1/stocks/search?q={query}` | Search stocks |
| GET | `/api/v1/sectors` | Get sector aggregation |
| GET | `/api/v1/market/fear-greed` | Get current Fear & Greed |
| GET | `/api/v1/experiment` | Get experiment results |
| GET | `/api/v1/experiment/week/{week}` | Get specific week results |
| GET | `/api/v1/methodology` | Get methodology content |

### 6.2 Response Examples

**GET /api/v1/stocks/top10**
```json
{
  "updated_at": "2026-01-02T06:30:00Z",
  "fear_greed": {
    "score": 38,
    "classification": "Fear",
    "change": -2
  },
  "stocks": [
    {
      "rank": 1,
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "nlp_score": 0.72,
      "nlp_momentum": 0.08,
      "calendar_score": 0.65,
      "combined_score": 0.69,
      "signal": "BUY",
      "conflict_flag": false
    }
  ]
}
```

**GET /api/v1/stocks/AAPL**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "price": {
    "current": 178.52,
    "change": 2.3,
    "change_percent": 1.31
  },
  "sentiment": {
    "nlp_score": 0.72,
    "nlp_momentum": 0.08,
    "nlp_trend": "3-day upward",
    "calendar_score": 0.65,
    "combined_score": 0.69,
    "signal": "BUY",
    "confidence": 0.73
  },
  "nlp_breakdown": {
    "news_score": 0.68,
    "news_count": 12,
    "reddit_score": 0.75,
    "reddit_count": 23,
    "topics": ["iPhone", "AI", "Services", "China"]
  },
  "calendar_breakdown": {
    "month_avg_return": 3.2,
    "month_win_rate": 0.67,
    "days_to_earnings": 45,
    "pattern_description": "Historically strong January"
  },
  "explainability": {
    "top_features": [
      {"feature": "sentiment_momentum", "contribution": 0.18},
      {"feature": "january_avg_return", "contribution": 0.15},
      {"feature": "article_volume", "contribution": 0.11}
    ]
  },
  "conflict": null,
  "updated_at": "2026-01-02T06:30:00Z"
}
```

---

## 7. Implementation Phases

### Phase 0: Foundation (Days 1-5)
**Goal:** Infrastructure and project scaffold

| Task | Duration | Deliverable |
|------|----------|-------------|
| AWS setup (EC2, RDS, S3) | 2 days | Running infrastructure |
| Project structure | 0.5 day | Python package scaffold |
| Database schema | 0.5 day | PostgreSQL tables created |
| Basic FastAPI app | 1 day | Health endpoint working |
| Basic Streamlit app | 1 day | Placeholder UI |

**Exit Criteria:**
- [ ] EC2 instance accessible via SSH
- [ ] RDS PostgreSQL connection working
- [ ] S3 bucket created with test upload
- [ ] FastAPI `/health` returns 200
- [ ] Streamlit displays "Hello World"

---

### Phase 1: Data Pipeline (Days 6-12)
**Goal:** Complete data ingestion and storage

| Task | Duration | Deliverable |
|------|----------|-------------|
| S&P 500 stock list ingestion | 0.5 day | dim_stocks populated |
| Calendar dimension setup | 0.5 day | dim_calendar populated |
| News API client | 1 day | Raw news stored in S3 |
| Reddit client (PRAW) | 1 day | Raw Reddit data in S3 |
| Price data client | 0.5 day | Yahoo Finance integration |
| Text cleaning pipeline | 1 day | Clean text extraction |
| Ticker extraction | 0.5 day | Map articles to stocks |
| Scheduler setup | 1 day | APScheduler running daily |
| Pipeline monitoring | 0.5 day | Logging and error handling |

**Exit Criteria:**
- [ ] Daily pipeline runs at 6 AM
- [ ] Raw data stored in S3 with date partitions
- [ ] Clean data loaded to staging tables
- [ ] Pipeline logs accessible

---

### Phase 2: Scoring Engine (Days 13-19)
**Goal:** NLP and Calendar scoring operational

| Task | Duration | Deliverable |
|------|----------|-------------|
| FinBERT integration | 2 days | Sentiment scores generated |
| Calendar pattern calculator | 2 days | 18-month patterns computed |
| Signal combination logic | 1 day | Combined scores |
| Momentum calculation | 0.5 day | Daily deltas computed |
| Conflict detection | 0.5 day | Conflict flags set |
| Fear & Greed scraper | 0.5 day | Daily F&G score |
| Topic extraction | 0.5 day | Keyword extraction |
| Fact table population | 0.5 day | fact_sentiment filled |

**Exit Criteria:**
- [ ] All S&P 500 stocks have daily scores
- [ ] Momentum tracked over 3+ days
- [ ] Conflict detection working
- [ ] Fear & Greed updating daily

---

### Phase 3: API & Dashboard (Days 20-26)
**Goal:** User-facing application complete

| Task | Duration | Deliverable |
|------|----------|-------------|
| FastAPI endpoints | 2 days | All endpoints working |
| Streamlit Dashboard | 2 days | Top 10 + F&G display |
| Stock Detail page | 1 day | Full detail view |
| Search functionality | 0.5 day | Search working |
| Sector aggregation | 0.5 day | Sector view |
| Methodology page | 0.5 day | Static content |
| Testing & bug fixes | 0.5 day | Stable beta |

**Exit Criteria (BETA COMPLETE):**
- [ ] Dashboard loads in <3 seconds
- [ ] All 503 S&P stocks searchable
- [ ] Stock detail shows all components
- [ ] Sector view displays correctly
- [ ] Mobile-responsive layout

---

### Phase 4: Experiment & Polish (Days 27-40)
**Goal:** Live experiment and full release

| Task | Duration | Deliverable |
|------|----------|-------------|
| Experiment table setup | 0.5 day | fact_experiment ready |
| LLM prompt engineering | 1 day | Standardized prompts |
| Weekly experiment script | 1 day | Automated tracking |
| Experiment dashboard | 1.5 days | Results display |
| Backtest implementation | 2 days | Historical performance |
| Research paper draft | 2 days | Methodology documented |
| XGBoost training pipeline | 2 days | Model retraining |
| SHAP integration | 1 day | Explainability charts |
| Final polish & testing | 2 days | Production ready |

**Exit Criteria (FULL RELEASE):**
- [ ] Experiment tracking live
- [ ] Backtest results displayed
- [ ] Research paper published on site
- [ ] All features documented

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API rate limits hit | High | Medium | Implement caching, stagger requests |
| FinBERT slow inference | Medium | Medium | Batch processing, async |
| AWS costs exceed budget | Medium | High | Monitor usage, set alerts |
| LLM API changes | Low | Medium | Abstract LLM calls, easy to swap |
| Data source unavailable | Medium | High | Multiple redundant sources |
| Model overfitting | Medium | Medium | Walk-forward validation |
| Scope creep | High | High | Strict phase adherence |

---

## 9. Budget Estimate (Monthly)

| Resource | Service | Cost |
|----------|---------|------|
| Compute | EC2 t3.medium | ~$30 |
| Database | RDS db.t3.micro | ~$15 |
| Storage | S3 (5GB) | ~$0.12 |
| Data Transfer | AWS | ~$5 |
| **Total** | | **~$50/month** |

*Note: Free tier may reduce costs further for first 12 months*

---

## 10. Success Criteria

### Beta (4 weeks)
- [ ] Dashboard displays Top 10 stocks with scores
- [ ] Search works for all S&P 500 stocks
- [ ] Daily data pipeline running reliably
- [ ] All Category A enhancements implemented
- [ ] Methodology page complete

### Full Release (8 weeks)
- [ ] Live experiment running for 8 weeks
- [ ] Backtest results displayed
- [ ] Research paper published
- [ ] LLM comparison complete
- [ ] All documentation interview-ready

### Portfolio Success
- [ ] Can explain architecture in interview
- [ ] Can defend technical decisions
- [ ] Code quality passes review
- [ ] System demonstrates DA/DE/DS skills

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **FinBERT** | BERT model fine-tuned on financial text |
| **GICS** | Global Industry Classification Standard |
| **NLP** | Natural Language Processing |
| **SHAP** | SHapley Additive exPlanations (model explainability) |
| **Walk-forward** | Backtesting method that prevents lookahead bias |
| **Fear & Greed Index** | Market sentiment indicator (0-100 scale) |
| **Sentiment Momentum** | Rate of change in sentiment score |
| **Signal Conflict** | When NLP and Calendar scores disagree |

---

## Appendix B: References

See `SEN2NAL_RESEARCH_KNOWLEDGE_BASE.md` for 47 academic and industry sources informing this design.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Faisal | Initial PRD creation |

---

**Approval:**
- [ ] Technical approach reviewed
- [ ] Phase scope agreed
- [ ] Ready to begin Phase 0
