# Sen2Nal: Database Schema Documentation

**Version:** 1.0  
**Author:** Faisal  
**Database:** PostgreSQL 15+  
**Created:** January 2026

---

## 1. Schema Overview

Sen2Nal uses a star schema design optimized for analytical queries. The schema consists of:
- **Dimension Tables**: Static/slowly changing reference data
- **Fact Tables**: Transactional/event data with metrics

```
                    ┌─────────────────┐
                    │  dim_calendar   │
                    └────────┬────────┘
                             │
┌─────────────────┐          │          ┌─────────────────┐
│  dim_stocks     │──────────┼──────────│ dim_fear_greed  │
└────────┬────────┘          │          └────────┬────────┘
         │                   │                   │
         │    ┌──────────────┴──────────────┐    │
         │    │                             │    │
         ▼    ▼                             ▼    ▼
┌─────────────────────┐         ┌─────────────────────┐
│   fact_sentiment    │         │    fact_prices      │
└─────────────────────┘         └─────────────────────┘
         │
         │
         ▼
┌─────────────────────┐         ┌─────────────────────┐
│  fact_predictions   │         │  fact_experiment    │
└─────────────────────┘         └─────────────────────┘
```

---

## 2. Dimension Tables

### 2.1 dim_stocks

**Purpose:** S&P 500 stock master data

```sql
CREATE TABLE dim_stocks (
    stock_id        SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL UNIQUE,
    company_name    VARCHAR(255) NOT NULL,
    sector          VARCHAR(100) NOT NULL,
    industry        VARCHAR(100),
    market_cap      BIGINT,                    -- In USD
    sp500_rank      INTEGER,                   -- 1-500 by market cap
    cik             VARCHAR(20),               -- SEC identifier
    isin            VARCHAR(20),               -- International identifier
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_dim_stocks_ticker ON dim_stocks(ticker);
CREATE INDEX idx_dim_stocks_sector ON dim_stocks(sector);
CREATE INDEX idx_dim_stocks_rank ON dim_stocks(sp500_rank);

-- Sample Data
INSERT INTO dim_stocks (ticker, company_name, sector, market_cap, sp500_rank) VALUES
('AAPL', 'Apple Inc.', 'Technology', 2800000000000, 1),
('MSFT', 'Microsoft Corporation', 'Technology', 2700000000000, 2),
('GOOGL', 'Alphabet Inc.', 'Communication Services', 1800000000000, 3),
('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 1700000000000, 4),
('NVDA', 'NVIDIA Corporation', 'Technology', 1200000000000, 5),
('META', 'Meta Platforms Inc.', 'Communication Services', 900000000000, 6),
('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 800000000000, 7),
('BRK.B', 'Berkshire Hathaway Inc.', 'Financials', 780000000000, 8),
('JPM', 'JPMorgan Chase & Co.', 'Financials', 500000000000, 9),
('V', 'Visa Inc.', 'Financials', 480000000000, 10);
```

### 2.2 dim_calendar

**Purpose:** Date dimension for time-based analysis

```sql
CREATE TABLE dim_calendar (
    date_id             SERIAL PRIMARY KEY,
    date                DATE NOT NULL UNIQUE,
    day_of_week         INTEGER NOT NULL,      -- 0=Monday, 6=Sunday
    day_of_week_name    VARCHAR(10) NOT NULL,
    day_of_month        INTEGER NOT NULL,
    week_of_year        INTEGER NOT NULL,
    month               INTEGER NOT NULL,
    month_name          VARCHAR(10) NOT NULL,
    quarter             INTEGER NOT NULL,
    year                INTEGER NOT NULL,
    is_weekend          BOOLEAN NOT NULL,
    is_trading_day      BOOLEAN NOT NULL,
    is_month_start      BOOLEAN NOT NULL,
    is_month_end        BOOLEAN NOT NULL,
    is_quarter_start    BOOLEAN NOT NULL,
    is_quarter_end      BOOLEAN NOT NULL,
    is_year_start       BOOLEAN NOT NULL,
    is_year_end         BOOLEAN NOT NULL,
    is_us_holiday       BOOLEAN DEFAULT FALSE,
    holiday_name        VARCHAR(50),
    -- Pre-calculated for calendar features
    trading_days_in_month INTEGER,
    trading_day_of_month  INTEGER
);

-- Indexes
CREATE INDEX idx_dim_calendar_date ON dim_calendar(date);
CREATE INDEX idx_dim_calendar_year_month ON dim_calendar(year, month);
CREATE INDEX idx_dim_calendar_trading ON dim_calendar(is_trading_day);

-- Generate calendar data (2024-2027)
-- This would typically be done via a script, example for a few dates:
INSERT INTO dim_calendar (
    date, day_of_week, day_of_week_name, day_of_month, week_of_year,
    month, month_name, quarter, year, is_weekend, is_trading_day,
    is_month_start, is_month_end, is_quarter_start, is_quarter_end,
    is_year_start, is_year_end
) VALUES
('2026-01-02', 4, 'Friday', 2, 1, 1, 'January', 1, 2026, FALSE, TRUE,
 FALSE, FALSE, FALSE, FALSE, FALSE, FALSE);
```

### 2.3 dim_fear_greed

**Purpose:** Daily market-wide Fear & Greed index

```sql
CREATE TABLE dim_fear_greed (
    fg_id               SERIAL PRIMARY KEY,
    date_id             INTEGER NOT NULL REFERENCES dim_calendar(date_id),
    date                DATE NOT NULL,
    score               INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    classification      VARCHAR(20) NOT NULL,  -- 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'
    prev_score          INTEGER,
    score_change        INTEGER,
    -- Component scores (if available)
    market_momentum     INTEGER,
    stock_price_strength INTEGER,
    stock_price_breadth INTEGER,
    put_call_ratio      DECIMAL(5,3),
    market_volatility   DECIMAL(5,2),
    safe_haven_demand   INTEGER,
    junk_bond_demand    INTEGER,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- Index
CREATE INDEX idx_dim_fear_greed_date ON dim_fear_greed(date DESC);

-- Classification enum
COMMENT ON COLUMN dim_fear_greed.classification IS 
'Values: Extreme Fear (0-25), Fear (25-45), Neutral (45-55), Greed (55-75), Extreme Greed (75-100)';
```

---

## 3. Fact Tables

### 3.1 fact_sentiment

**Purpose:** Daily sentiment scores per stock (main analytical table)

```sql
CREATE TABLE fact_sentiment (
    sentiment_id        SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES dim_stocks(stock_id),
    date_id             INTEGER NOT NULL REFERENCES dim_calendar(date_id),
    
    -- NLP Sentiment Scores
    nlp_score           DECIMAL(5,4) NOT NULL,  -- -1.0 to 1.0
    nlp_score_prev      DECIMAL(5,4),           -- Previous day score
    nlp_momentum        DECIMAL(5,4),           -- Change from previous day
    nlp_trend_days      INTEGER DEFAULT 0,      -- Consecutive days in same direction
    nlp_confidence      DECIMAL(4,3),           -- 0 to 1
    
    -- Source Breakdown
    news_score          DECIMAL(5,4),
    news_count          INTEGER DEFAULT 0,
    reddit_score        DECIMAL(5,4),
    reddit_count        INTEGER DEFAULT 0,
    
    -- Calendar Pattern Score
    calendar_score      DECIMAL(5,4) NOT NULL,  -- -1.0 to 1.0
    month_avg_return    DECIMAL(6,3),           -- Historical month avg %
    month_win_rate      DECIMAL(4,3),           -- 0 to 1
    days_to_earnings    INTEGER,                -- NULL if unknown
    
    -- Combined Signal
    combined_score      DECIMAL(4,3) NOT NULL,  -- 0 to 1 (normalized)
    signal              VARCHAR(20) NOT NULL,   -- 'STRONG_BUY', 'BUY', 'HOLD', 'AVOID'
    confidence          DECIMAL(4,3) NOT NULL,  -- 0 to 1
    
    -- Conflict Detection
    conflict_flag       BOOLEAN DEFAULT FALSE,
    conflict_reason     TEXT,
    
    -- Topics/Keywords
    topics              JSONB,                  -- ["iPhone", "AI", "earnings"]
    
    -- Metadata
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id     VARCHAR(50),            -- For debugging
    
    UNIQUE(stock_id, date_id)
);

-- Indexes for common queries
CREATE INDEX idx_fact_sentiment_stock_date ON fact_sentiment(stock_id, date_id DESC);
CREATE INDEX idx_fact_sentiment_date ON fact_sentiment(date_id DESC);
CREATE INDEX idx_fact_sentiment_signal ON fact_sentiment(signal);
CREATE INDEX idx_fact_sentiment_combined ON fact_sentiment(combined_score DESC);
CREATE INDEX idx_fact_sentiment_conflict ON fact_sentiment(conflict_flag) WHERE conflict_flag = TRUE;

-- Partial index for recent data (faster dashboard queries)
CREATE INDEX idx_fact_sentiment_recent ON fact_sentiment(date_id DESC, stock_id)
WHERE date_id >= (SELECT date_id FROM dim_calendar WHERE date = CURRENT_DATE - INTERVAL '30 days');
```

### 3.2 fact_prices

**Purpose:** Daily OHLCV price data

```sql
CREATE TABLE fact_prices (
    price_id            SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES dim_stocks(stock_id),
    date_id             INTEGER NOT NULL REFERENCES dim_calendar(date_id),
    date                DATE NOT NULL,
    
    -- OHLCV Data
    open                DECIMAL(12,4) NOT NULL,
    high                DECIMAL(12,4) NOT NULL,
    low                 DECIMAL(12,4) NOT NULL,
    close               DECIMAL(12,4) NOT NULL,
    adj_close           DECIMAL(12,4) NOT NULL,
    volume              BIGINT NOT NULL,
    
    -- Calculated Fields
    daily_return        DECIMAL(8,5),           -- (close - prev_close) / prev_close
    intraday_range      DECIMAL(8,5),           -- (high - low) / open
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, date_id)
);

-- Indexes
CREATE INDEX idx_fact_prices_stock_date ON fact_prices(stock_id, date_id DESC);
CREATE INDEX idx_fact_prices_date ON fact_prices(date_id DESC);
```

### 3.3 fact_predictions

**Purpose:** Store model predictions for backtesting and evaluation

```sql
CREATE TABLE fact_predictions (
    prediction_id       SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES dim_stocks(stock_id),
    date_id             INTEGER NOT NULL REFERENCES dim_calendar(date_id),
    prediction_date     DATE NOT NULL,          -- When prediction was made
    target_date         DATE NOT NULL,          -- Date being predicted (usually +5 days)
    
    -- Prediction
    predicted_direction VARCHAR(10) NOT NULL,   -- 'UP', 'DOWN', 'NEUTRAL'
    predicted_score     DECIMAL(4,3) NOT NULL,  -- 0 to 1
    predicted_confidence DECIMAL(4,3) NOT NULL,
    
    -- Actual Outcome (filled after target_date)
    actual_direction    VARCHAR(10),
    actual_return       DECIMAL(8,5),
    prediction_correct  BOOLEAN,
    
    -- Model Info
    model_version       VARCHAR(20) NOT NULL,
    feature_importance  JSONB,                  -- Top features for this prediction
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluated_at        TIMESTAMP,
    
    UNIQUE(stock_id, prediction_date, target_date)
);

-- Indexes
CREATE INDEX idx_fact_predictions_stock_date ON fact_predictions(stock_id, prediction_date DESC);
CREATE INDEX idx_fact_predictions_evaluation ON fact_predictions(target_date) 
WHERE actual_direction IS NULL;
```

### 3.4 fact_experiment

**Purpose:** Track Sen2Nal vs LLM weekly experiment

```sql
CREATE TABLE fact_experiment (
    experiment_id       SERIAL PRIMARY KEY,
    week_number         INTEGER NOT NULL,       -- 1-52
    year                INTEGER NOT NULL,
    method              VARCHAR(20) NOT NULL,   -- 'SEN2NAL', 'CHATGPT', 'GEMINI', 'GROK'
    
    -- Monday Entry
    entry_date          DATE NOT NULL,
    stock_1_ticker      VARCHAR(10) NOT NULL,
    stock_1_score       DECIMAL(4,3),           -- NULL for LLMs
    stock_1_entry       DECIMAL(12,4),          -- Monday open price
    stock_1_reasoning   TEXT,                   -- LLM reasoning text
    
    stock_2_ticker      VARCHAR(10) NOT NULL,
    stock_2_score       DECIMAL(4,3),
    stock_2_entry       DECIMAL(12,4),
    stock_2_reasoning   TEXT,
    
    stock_3_ticker      VARCHAR(10) NOT NULL,
    stock_3_score       DECIMAL(4,3),
    stock_3_entry       DECIMAL(12,4),
    stock_3_reasoning   TEXT,
    
    -- Friday Exit (filled end of week)
    exit_date           DATE,
    stock_1_exit        DECIMAL(12,4),          -- Friday close price
    stock_2_exit        DECIMAL(12,4),
    stock_3_exit        DECIMAL(12,4),
    
    -- Performance
    stock_1_return      DECIMAL(8,5),           -- (exit - entry) / entry
    stock_2_return      DECIMAL(8,5),
    stock_3_return      DECIMAL(8,5),
    weekly_return       DECIMAL(8,5),           -- Average of 3 stocks
    
    -- Winner Flag
    is_winner           BOOLEAN DEFAULT FALSE,
    
    -- LLM Details
    llm_prompt          TEXT,                   -- Prompt used
    llm_response        TEXT,                   -- Raw response
    llm_model_version   VARCHAR(50),            -- e.g., 'gpt-4-0125-preview'
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(year, week_number, method)
);

-- Indexes
CREATE INDEX idx_fact_experiment_week ON fact_experiment(year DESC, week_number DESC);
CREATE INDEX idx_fact_experiment_method ON fact_experiment(method);
CREATE INDEX idx_fact_experiment_winner ON fact_experiment(is_winner) WHERE is_winner = TRUE;
```

---

## 4. Staging Tables

### 4.1 stg_news_raw

**Purpose:** Raw news articles before processing

```sql
CREATE TABLE stg_news_raw (
    raw_id              SERIAL PRIMARY KEY,
    source              VARCHAR(50) NOT NULL,   -- 'alpha_vantage', 'newsapi', 'yahoo'
    external_id         VARCHAR(100),           -- Source's article ID
    headline            TEXT NOT NULL,
    summary             TEXT,
    url                 TEXT,
    published_at        TIMESTAMP,
    fetched_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Processing Status
    is_processed        BOOLEAN DEFAULT FALSE,
    processed_at        TIMESTAMP,
    
    -- Extracted Data (filled during processing)
    tickers_mentioned   TEXT[],                 -- Array of tickers found
    sentiment_score     DECIMAL(5,4),
    sentiment_label     VARCHAR(20),
    
    -- Deduplication
    content_hash        VARCHAR(64),            -- SHA256 of headline
    is_duplicate        BOOLEAN DEFAULT FALSE,
    
    UNIQUE(source, external_id)
);

-- Indexes
CREATE INDEX idx_stg_news_unprocessed ON stg_news_raw(is_processed, fetched_at)
WHERE is_processed = FALSE;
CREATE INDEX idx_stg_news_hash ON stg_news_raw(content_hash);
```

### 4.2 stg_reddit_raw

**Purpose:** Raw Reddit posts before processing

```sql
CREATE TABLE stg_reddit_raw (
    raw_id              SERIAL PRIMARY KEY,
    subreddit           VARCHAR(50) NOT NULL,   -- 'stocks', 'wallstreetbets'
    post_id             VARCHAR(20) NOT NULL,
    post_type           VARCHAR(20) NOT NULL,   -- 'submission', 'comment'
    title               TEXT,
    body                TEXT,
    author              VARCHAR(50),
    score               INTEGER,                -- Reddit upvotes
    num_comments        INTEGER,
    created_utc         TIMESTAMP,
    fetched_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Processing Status
    is_processed        BOOLEAN DEFAULT FALSE,
    processed_at        TIMESTAMP,
    
    -- Extracted Data
    tickers_mentioned   TEXT[],
    sentiment_score     DECIMAL(5,4),
    sentiment_label     VARCHAR(20),
    
    UNIQUE(subreddit, post_id)
);

-- Index
CREATE INDEX idx_stg_reddit_unprocessed ON stg_reddit_raw(is_processed, fetched_at)
WHERE is_processed = FALSE;
```

---

## 5. Materialized Views

### 5.1 mv_top10_stocks

**Purpose:** Pre-computed top 10 stocks for fast dashboard loading

```sql
CREATE MATERIALIZED VIEW mv_top10_stocks AS
SELECT 
    s.stock_id,
    s.ticker,
    s.company_name,
    s.sector,
    s.sp500_rank,
    fs.nlp_score,
    fs.nlp_momentum,
    fs.calendar_score,
    fs.combined_score,
    fs.signal,
    fs.confidence,
    fs.conflict_flag,
    fs.topics,
    c.date AS score_date,
    p.close AS current_price,
    p.daily_return
FROM dim_stocks s
JOIN fact_sentiment fs ON s.stock_id = fs.stock_id
JOIN dim_calendar c ON fs.date_id = c.date_id
LEFT JOIN fact_prices p ON s.stock_id = p.stock_id AND fs.date_id = p.date_id
WHERE s.sp500_rank <= 10
  AND c.date = (SELECT MAX(date) FROM dim_calendar dc 
                JOIN fact_sentiment fs2 ON dc.date_id = fs2.date_id)
ORDER BY s.sp500_rank;

-- Refresh daily after pipeline
CREATE INDEX idx_mv_top10_rank ON mv_top10_stocks(sp500_rank);

-- Refresh command (run after daily pipeline)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top10_stocks;
```

### 5.2 mv_sector_sentiment

**Purpose:** Aggregated sentiment by sector

```sql
CREATE MATERIALIZED VIEW mv_sector_sentiment AS
SELECT 
    s.sector,
    COUNT(*) AS stock_count,
    AVG(fs.combined_score) AS avg_combined_score,
    AVG(fs.nlp_score) AS avg_nlp_score,
    AVG(fs.calendar_score) AS avg_calendar_score,
    SUM(CASE WHEN fs.signal IN ('BUY', 'STRONG_BUY') THEN 1 ELSE 0 END) AS bullish_count,
    SUM(CASE WHEN fs.signal = 'AVOID' THEN 1 ELSE 0 END) AS bearish_count,
    SUM(CASE WHEN fs.signal = 'HOLD' THEN 1 ELSE 0 END) AS neutral_count,
    c.date AS score_date
FROM dim_stocks s
JOIN fact_sentiment fs ON s.stock_id = fs.stock_id
JOIN dim_calendar c ON fs.date_id = c.date_id
WHERE c.date = (SELECT MAX(date) FROM dim_calendar dc 
                JOIN fact_sentiment fs2 ON dc.date_id = fs2.date_id)
GROUP BY s.sector, c.date
ORDER BY avg_combined_score DESC;

CREATE INDEX idx_mv_sector_score ON mv_sector_sentiment(avg_combined_score DESC);
```

---

## 6. Common Queries

### 6.1 Get Today's Top 10 Stocks

```sql
SELECT * FROM mv_top10_stocks;
```

### 6.2 Get Stock Detail

```sql
SELECT 
    s.ticker,
    s.company_name,
    s.sector,
    fs.nlp_score,
    fs.nlp_momentum,
    fs.nlp_confidence,
    fs.news_score,
    fs.news_count,
    fs.reddit_score,
    fs.reddit_count,
    fs.calendar_score,
    fs.month_avg_return,
    fs.month_win_rate,
    fs.days_to_earnings,
    fs.combined_score,
    fs.signal,
    fs.confidence,
    fs.conflict_flag,
    fs.conflict_reason,
    fs.topics,
    p.close AS current_price,
    p.daily_return,
    fg.score AS fear_greed_score,
    fg.classification AS fear_greed_class
FROM dim_stocks s
JOIN fact_sentiment fs ON s.stock_id = fs.stock_id
JOIN dim_calendar c ON fs.date_id = c.date_id
LEFT JOIN fact_prices p ON s.stock_id = p.stock_id AND fs.date_id = p.date_id
LEFT JOIN dim_fear_greed fg ON c.date = fg.date
WHERE s.ticker = 'AAPL'
  AND c.date = (SELECT MAX(date) FROM dim_calendar dc 
                JOIN fact_sentiment fs2 ON dc.date_id = fs2.date_id);
```

### 6.3 Get Sentiment History for Stock

```sql
SELECT 
    c.date,
    fs.nlp_score,
    fs.calendar_score,
    fs.combined_score,
    fs.signal,
    p.adj_close,
    p.daily_return
FROM fact_sentiment fs
JOIN dim_calendar c ON fs.date_id = c.date_id
JOIN dim_stocks s ON fs.stock_id = s.stock_id
LEFT JOIN fact_prices p ON fs.stock_id = p.stock_id AND fs.date_id = p.date_id
WHERE s.ticker = 'AAPL'
  AND c.date >= CURRENT_DATE - INTERVAL '18 months'
ORDER BY c.date;
```

### 6.4 Get Experiment Results

```sql
SELECT 
    year,
    week_number,
    method,
    stock_1_ticker,
    stock_2_ticker,
    stock_3_ticker,
    weekly_return,
    is_winner
FROM fact_experiment
WHERE year = 2026
ORDER BY week_number, method;

-- Cumulative totals
SELECT 
    method,
    COUNT(*) AS total_weeks,
    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
    ROUND(AVG(weekly_return) * 100, 2) AS avg_weekly_return_pct,
    ROUND(SUM(weekly_return) * 100, 2) AS total_return_pct
FROM fact_experiment
WHERE year = 2026
GROUP BY method
ORDER BY total_return_pct DESC;
```

### 6.5 Get Sector Aggregation

```sql
SELECT * FROM mv_sector_sentiment
ORDER BY avg_combined_score DESC;
```

---

## 7. Database Maintenance

### 7.1 Refresh Materialized Views

```sql
-- Run daily after pipeline completion
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top10_stocks;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sector_sentiment;
```

### 7.2 Cleanup Old Staging Data

```sql
-- Delete processed staging data older than 7 days
DELETE FROM stg_news_raw 
WHERE is_processed = TRUE 
  AND processed_at < CURRENT_DATE - INTERVAL '7 days';

DELETE FROM stg_reddit_raw 
WHERE is_processed = TRUE 
  AND processed_at < CURRENT_DATE - INTERVAL '7 days';
```

### 7.3 Vacuum and Analyze

```sql
-- Run weekly
VACUUM ANALYZE fact_sentiment;
VACUUM ANALYZE fact_prices;
VACUUM ANALYZE fact_predictions;
```

---

## 8. Alembic Migration Example

```python
# migrations/versions/001_initial_schema.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None

def upgrade():
    # Create dim_stocks
    op.create_table(
        'dim_stocks',
        sa.Column('stock_id', sa.Integer(), primary_key=True),
        sa.Column('ticker', sa.String(10), nullable=False, unique=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('sector', sa.String(100), nullable=False),
        sa.Column('industry', sa.String(100)),
        sa.Column('market_cap', sa.BigInteger()),
        sa.Column('sp500_rank', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_dim_stocks_ticker', 'dim_stocks', ['ticker'])
    
    # Create dim_calendar
    op.create_table(
        'dim_calendar',
        sa.Column('date_id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('is_trading_day', sa.Boolean(), nullable=False)
    )
    op.create_index('idx_dim_calendar_date', 'dim_calendar', ['date'])
    
    # ... continue for all tables

def downgrade():
    op.drop_table('dim_stocks')
    op.drop_table('dim_calendar')
    # ... continue for all tables
```

---

## 9. Connection Configuration

```python
# src/database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sen2nal_admin:password@localhost:5432/sen2nal"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False  # Set True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

This schema is designed for:
- **Performance**: Indexed for common query patterns
- **Scalability**: Star schema allows easy expansion
- **Maintainability**: Clear separation of concerns
- **Analytics**: Optimized for sentiment analysis queries
