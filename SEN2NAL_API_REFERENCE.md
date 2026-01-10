# Sen2Nal: API Reference Documentation

**Version:** 1.0  
**Base URL:** `https://sen2nal.yourdomain.com/api/v1`  
**Authentication:** None (public API for MVP)  
**Format:** JSON

---

## Overview

Sen2Nal API provides programmatic access to stock sentiment analysis, calendar patterns, and experiment results. All endpoints return JSON responses.

### Response Format

All successful responses follow this structure:
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-01-02T06:30:00Z",
    "version": "1.0"
  }
}
```

Error responses:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Stock ticker 'INVALID' not found in S&P 500",
    "details": null
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 429 | Rate Limited - Too many requests |
| 500 | Internal Server Error |

---

## Endpoints

### Health Check

#### GET /health

Check API server status.

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "last_pipeline_run": "2026-01-02T06:30:00Z",
  "uptime_seconds": 86400
}
```

---

### Stocks

#### GET /stocks

List all tracked stocks (S&P 500).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| sector | string | null | Filter by sector |
| signal | string | null | Filter by signal (STRONG_BUY, BUY, HOLD, AVOID) |
| limit | int | 50 | Max results (1-500) |
| offset | int | 0 | Pagination offset |

**Request:**
```bash
curl "https://sen2nal.yourdomain.com/api/v1/stocks?sector=Technology&limit=10"
```

**Response:**
```json
{
  "data": {
    "stocks": [
      {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "sp500_rank": 1,
        "combined_score": 0.69,
        "signal": "BUY"
      },
      {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "sp500_rank": 2,
        "combined_score": 0.71,
        "signal": "STRONG_BUY"
      }
    ],
    "total": 75,
    "limit": 10,
    "offset": 0
  }
}
```

---

#### GET /stocks/top10

Get top 10 stocks by market cap with full sentiment data.

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/stocks/top10
```

**Response:**
```json
{
  "data": {
    "updated_at": "2026-01-02T06:30:00Z",
    "fear_greed": {
      "score": 38,
      "classification": "Fear",
      "change": -2,
      "updated_at": "2026-01-02T06:00:00Z"
    },
    "stocks": [
      {
        "rank": 1,
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "nlp_score": 0.72,
        "nlp_momentum": 0.08,
        "calendar_score": 0.65,
        "combined_score": 0.69,
        "signal": "BUY",
        "confidence": 0.73,
        "conflict_flag": false,
        "current_price": 178.52,
        "daily_change_pct": 1.31
      },
      {
        "rank": 2,
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "nlp_score": 0.68,
        "nlp_momentum": 0.05,
        "calendar_score": 0.71,
        "combined_score": 0.69,
        "signal": "BUY",
        "confidence": 0.78,
        "conflict_flag": false,
        "current_price": 412.30,
        "daily_change_pct": 0.85
      }
    ]
  }
}
```

---

#### GET /stocks/search

Search stocks by ticker or company name.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (min 1 char) |
| limit | int | No | Max results (default: 10) |

**Request:**
```bash
curl "https://sen2nal.yourdomain.com/api/v1/stocks/search?q=apple"
```

**Response:**
```json
{
  "data": {
    "results": [
      {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "match_type": "company_name"
      }
    ],
    "query": "apple",
    "count": 1
  }
}
```

---

#### GET /stocks/{ticker}

Get detailed sentiment analysis for a specific stock.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| ticker | string | Stock ticker (e.g., AAPL) |

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/stocks/AAPL
```

**Response:**
```json
{
  "data": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology",
    "sp500_rank": 1,
    
    "price": {
      "current": 178.52,
      "open": 176.20,
      "high": 179.10,
      "low": 175.80,
      "change": 2.32,
      "change_percent": 1.31,
      "volume": 45200000
    },
    
    "sentiment": {
      "nlp_score": 0.72,
      "nlp_momentum": 0.08,
      "nlp_trend": "3-day upward",
      "nlp_confidence": 0.78,
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
      "source_agreement": 0.82,
      "topics": [
        {"topic": "iPhone", "frequency": 0.34},
        {"topic": "AI", "frequency": 0.22},
        {"topic": "Services", "frequency": 0.15},
        {"topic": "China", "frequency": 0.10}
      ]
    },
    
    "calendar_breakdown": {
      "current_month": "January",
      "month_avg_return": 3.2,
      "month_win_rate": 0.67,
      "sample_months": 18,
      "days_to_earnings": 45,
      "pattern_description": "Historically strong January performance"
    },
    
    "explainability": {
      "top_features": [
        {"feature": "sentiment_momentum", "contribution": 0.18, "direction": "positive"},
        {"feature": "january_avg_return", "contribution": 0.15, "direction": "positive"},
        {"feature": "article_volume", "contribution": 0.11, "direction": "positive"},
        {"feature": "reddit_sentiment", "contribution": 0.09, "direction": "positive"},
        {"feature": "news_sentiment", "contribution": 0.07, "direction": "positive"}
      ]
    },
    
    "conflict": null,
    
    "updated_at": "2026-01-02T06:30:00Z"
  }
}
```

**Response with Conflict:**
```json
{
  "data": {
    "ticker": "TSLA",
    "...": "...",
    "conflict": {
      "detected": true,
      "nlp_signal": "Bullish",
      "nlp_score": 0.72,
      "calendar_signal": "Bearish",
      "calendar_score": 0.35,
      "score_difference": 0.37,
      "reason": "Strong news sentiment vs. historically weak January for TSLA",
      "historical_resolution": "Similar conflicts resolved toward NLP 60% of time"
    }
  }
}
```

---

#### GET /stocks/{ticker}/history

Get historical sentiment data for a stock.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| ticker | string | Stock ticker |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | int | 30 | Number of days (1-540) |

**Request:**
```bash
curl "https://sen2nal.yourdomain.com/api/v1/stocks/AAPL/history?days=90"
```

**Response:**
```json
{
  "data": {
    "ticker": "AAPL",
    "period_days": 90,
    "history": [
      {
        "date": "2026-01-02",
        "nlp_score": 0.72,
        "calendar_score": 0.65,
        "combined_score": 0.69,
        "signal": "BUY",
        "close_price": 178.52,
        "daily_return": 0.0131
      },
      {
        "date": "2025-12-31",
        "nlp_score": 0.64,
        "calendar_score": 0.68,
        "combined_score": 0.66,
        "signal": "BUY",
        "close_price": 176.20,
        "daily_return": -0.0052
      }
    ]
  }
}
```

---

### Sectors

#### GET /sectors

Get sentiment aggregated by sector.

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/sectors
```

**Response:**
```json
{
  "data": {
    "updated_at": "2026-01-02T06:30:00Z",
    "sectors": [
      {
        "sector": "Technology",
        "stock_count": 75,
        "avg_nlp_score": 0.58,
        "avg_calendar_score": 0.62,
        "avg_combined_score": 0.60,
        "bullish_count": 42,
        "bearish_count": 8,
        "neutral_count": 25,
        "top_stock": {
          "ticker": "NVDA",
          "combined_score": 0.78
        }
      },
      {
        "sector": "Healthcare",
        "stock_count": 65,
        "avg_nlp_score": 0.52,
        "avg_calendar_score": 0.55,
        "avg_combined_score": 0.53,
        "bullish_count": 28,
        "bearish_count": 12,
        "neutral_count": 25,
        "top_stock": {
          "ticker": "UNH",
          "combined_score": 0.71
        }
      }
    ]
  }
}
```

---

#### GET /sectors/{sector}

Get detailed sector information with constituent stocks.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| sector | string | Sector name (URL encoded) |

**Request:**
```bash
curl "https://sen2nal.yourdomain.com/api/v1/sectors/Technology"
```

**Response:**
```json
{
  "data": {
    "sector": "Technology",
    "updated_at": "2026-01-02T06:30:00Z",
    "summary": {
      "stock_count": 75,
      "avg_combined_score": 0.60,
      "sentiment_distribution": {
        "STRONG_BUY": 12,
        "BUY": 30,
        "HOLD": 25,
        "AVOID": 8
      }
    },
    "stocks": [
      {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "combined_score": 0.78,
        "signal": "STRONG_BUY"
      },
      {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "combined_score": 0.69,
        "signal": "BUY"
      }
    ]
  }
}
```

---

### Market

#### GET /market/fear-greed

Get current Fear & Greed Index.

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/market/fear-greed
```

**Response:**
```json
{
  "data": {
    "score": 38,
    "classification": "Fear",
    "description": "Investors are showing general caution with risk-off sentiment",
    "previous_score": 40,
    "change": -2,
    "updated_at": "2026-01-02T06:00:00Z",
    "history_7d": [
      {"date": "2026-01-02", "score": 38},
      {"date": "2026-01-01", "score": 40},
      {"date": "2025-12-31", "score": 42},
      {"date": "2025-12-30", "score": 45},
      {"date": "2025-12-27", "score": 48},
      {"date": "2025-12-26", "score": 44},
      {"date": "2025-12-24", "score": 41}
    ]
  }
}
```

---

#### GET /market/fear-greed/history

Get Fear & Greed historical data.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | int | 30 | Number of days (1-365) |

**Request:**
```bash
curl "https://sen2nal.yourdomain.com/api/v1/market/fear-greed/history?days=90"
```

**Response:**
```json
{
  "data": {
    "period_days": 90,
    "average_score": 52,
    "min_score": 25,
    "max_score": 78,
    "current_percentile": 35,
    "history": [
      {"date": "2026-01-02", "score": 38, "classification": "Fear"},
      {"date": "2026-01-01", "score": 40, "classification": "Fear"}
    ]
  }
}
```

---

### Experiment

#### GET /experiment

Get current experiment status and results.

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/experiment
```

**Response:**
```json
{
  "data": {
    "status": "LIVE",
    "current_week": 6,
    "total_weeks": 8,
    "experiment_start": "2025-11-25",
    "experiment_end": "2026-01-17",
    
    "this_week": {
      "week_number": 6,
      "entry_date": "2025-12-30",
      "exit_date": "2026-01-03",
      "status": "IN_PROGRESS",
      "picks": {
        "SEN2NAL": [
          {"ticker": "AAPL", "score": 0.69, "entry_price": 176.20},
          {"ticker": "MSFT", "score": 0.69, "entry_price": 410.50},
          {"ticker": "JPM", "score": 0.65, "entry_price": 193.20}
        ],
        "CHATGPT": [
          {"ticker": "NVDA", "reasoning": "Strong AI momentum", "entry_price": 872.30},
          {"ticker": "AAPL", "reasoning": "Services growth", "entry_price": 176.20},
          {"ticker": "GOOGL", "reasoning": "Search dominance", "entry_price": 140.80}
        ],
        "GEMINI": [
          {"ticker": "MSFT", "reasoning": "Cloud leadership", "entry_price": 410.50},
          {"ticker": "AMZN", "reasoning": "E-commerce recovery", "entry_price": 185.40},
          {"ticker": "META", "reasoning": "Ad revenue growth", "entry_price": 520.10}
        ],
        "GROK": [
          {"ticker": "GOOGL", "reasoning": "AI integration", "entry_price": 140.80},
          {"ticker": "AAPL", "reasoning": "iPhone cycle", "entry_price": 176.20},
          {"ticker": "NVDA", "reasoning": "GPU demand", "entry_price": 872.30}
        ]
      }
    },
    
    "cumulative_results": [
      {
        "week": 1,
        "results": {
          "SEN2NAL": {"return": 2.3, "winner": true},
          "CHATGPT": {"return": 1.1, "winner": false},
          "GEMINI": {"return": 1.8, "winner": false},
          "GROK": {"return": 0.9, "winner": false}
        }
      },
      {
        "week": 2,
        "results": {
          "SEN2NAL": {"return": -0.5, "winner": false},
          "CHATGPT": {"return": 0.8, "winner": false},
          "GEMINI": {"return": -0.2, "winner": false},
          "GROK": {"return": 1.2, "winner": true}
        }
      }
    ],
    
    "totals": {
      "SEN2NAL": {"total_return": 6.0, "wins": 3, "avg_weekly": 1.2},
      "CHATGPT": {"total_return": 4.9, "wins": 1, "avg_weekly": 0.98},
      "GEMINI": {"total_return": 5.2, "wins": 1, "avg_weekly": 1.04},
      "GROK": {"total_return": 4.1, "wins": 1, "avg_weekly": 0.82}
    },
    
    "leader": "SEN2NAL"
  }
}
```

---

#### GET /experiment/week/{week}

Get detailed results for a specific week.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| week | int | Week number (1-8) |

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/experiment/week/1
```

**Response:**
```json
{
  "data": {
    "week_number": 1,
    "year": 2025,
    "entry_date": "2025-11-25",
    "exit_date": "2025-11-29",
    "status": "COMPLETE",
    
    "methods": {
      "SEN2NAL": {
        "picks": [
          {
            "ticker": "NVDA",
            "score": 0.78,
            "entry_price": 485.20,
            "exit_price": 498.50,
            "return_pct": 2.74
          },
          {
            "ticker": "META",
            "score": 0.72,
            "entry_price": 505.10,
            "exit_price": 512.30,
            "return_pct": 1.42
          },
          {
            "ticker": "AAPL",
            "score": 0.70,
            "entry_price": 172.40,
            "exit_price": 177.20,
            "return_pct": 2.78
          }
        ],
        "weekly_return": 2.31,
        "is_winner": true
      },
      "CHATGPT": {
        "picks": [
          {
            "ticker": "MSFT",
            "reasoning": "Strong cloud growth expected",
            "entry_price": 378.50,
            "exit_price": 382.10,
            "return_pct": 0.95
          }
        ],
        "weekly_return": 1.10,
        "is_winner": false,
        "prompt_used": "You are a financial analyst...",
        "raw_response": "Based on current market conditions..."
      }
    },
    
    "winner": "SEN2NAL",
    "margin": 1.21
  }
}
```

---

### Methodology

#### GET /methodology

Get methodology documentation.

**Request:**
```bash
curl https://sen2nal.yourdomain.com/api/v1/methodology
```

**Response:**
```json
{
  "data": {
    "version": "1.0",
    "last_updated": "2026-01-01",
    
    "overview": "Sen2Nal combines NLP-based sentiment analysis with calendar pattern recognition...",
    
    "nlp_layer": {
      "model": "ProsusAI/finbert",
      "description": "FinBERT is a BERT model fine-tuned on financial text...",
      "score_range": "-1.0 (very negative) to +1.0 (very positive)",
      "sources": ["Alpha Vantage News", "Yahoo Finance", "Reddit r/stocks"]
    },
    
    "calendar_layer": {
      "description": "Historical analysis of monthly returns...",
      "lookback_period": "18 months",
      "factors": ["Monthly average returns", "Win rate", "Earnings proximity"]
    },
    
    "signal_combination": {
      "formula": "combined = (0.6 × NLP) + (0.4 × Calendar)",
      "thresholds": {
        "STRONG_BUY": "> 0.70",
        "BUY": "0.55 - 0.70",
        "HOLD": "0.45 - 0.55",
        "AVOID": "< 0.45"
      }
    },
    
    "limitations": [
      "Past performance does not guarantee future results",
      "Sentiment analysis has inherent accuracy limitations",
      "Calendar patterns may not repeat in changing market conditions",
      "Data limited to S&P 500 stocks"
    ],
    
    "research_paper_url": "/research/sen2nal-methodology.pdf"
  }
}
```

---

## Rate Limiting

| Tier | Requests/Minute | Requests/Day |
|------|-----------------|--------------|
| Free | 60 | 1000 |

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1704182460
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TICKER` | 400 | Ticker format is invalid |
| `STOCK_NOT_FOUND` | 404 | Stock not in S&P 500 |
| `SECTOR_NOT_FOUND` | 404 | Invalid sector name |
| `INVALID_DATE_RANGE` | 400 | Date range exceeds limits |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## SDKs & Examples

### Python Example

```python
import requests

BASE_URL = "https://sen2nal.yourdomain.com/api/v1"

# Get top 10 stocks
response = requests.get(f"{BASE_URL}/stocks/top10")
data = response.json()

for stock in data["data"]["stocks"]:
    print(f"{stock['ticker']}: {stock['signal']} ({stock['combined_score']:.2f})")

# Get specific stock
response = requests.get(f"{BASE_URL}/stocks/AAPL")
aapl = response.json()["data"]
print(f"AAPL NLP Score: {aapl['sentiment']['nlp_score']}")
print(f"AAPL Calendar Score: {aapl['sentiment']['calendar_score']}")
```

### cURL Examples

```bash
# Get top 10 stocks
curl https://sen2nal.yourdomain.com/api/v1/stocks/top10 | jq '.data.stocks[0]'

# Search for a stock
curl "https://sen2nal.yourdomain.com/api/v1/stocks/search?q=nvidia" | jq

# Get experiment results
curl https://sen2nal.yourdomain.com/api/v1/experiment | jq '.data.totals'
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial API release |

---

*For questions or issues, contact: faisal@yourdomain.com*
