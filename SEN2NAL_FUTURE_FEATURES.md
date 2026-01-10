# Sen2Nal: Future Features Roadmap

**Version:** 1.0  
**Author:** Faisal (Mohamad Faisal Bin Mohd Hanafi)  
**Created:** January 2026  
**Status:** Keep In View (KIV) for Future Versions

---

## Overview

This document contains detailed specifications for features that were identified during research but deferred from the initial release. These features are valuable additions that can be implemented in future versions based on user feedback and available development time.

**Categories:**
- **Category B**: Medium complexity features (3-5 days each)
- **Category C**: Nice-to-have features (2-4 days each)

---

## Category B Features

### B1: Informative vs Emotional Classification

**Priority:** Medium  
**Estimated Effort:** 3-4 days  
**Dependencies:** FinBERT implementation complete

#### Description
Distinguish between factual news content and emotional/hype content. This helps users understand whether sentiment is driven by substantive information or retail trader excitement.

#### Research Basis
> "We group the messages into two classes, as being either informative or emotional. Messages such as 'To the Moon! Let's get rich!' would be considered highly emotional, whilst 'X company has reported a loss in the final quarter' would be deemed informative."
> — StockGeist.ai

#### Technical Implementation

```python
# src/sentiment/emotional_classifier.py

from dataclasses import dataclass
from enum import Enum
import re

class ContentType(Enum):
    INFORMATIVE = "informative"
    EMOTIONAL = "emotional"
    MIXED = "mixed"

@dataclass
class ClassificationResult:
    content_type: ContentType
    informative_score: float  # 0 to 1
    emotional_score: float    # 0 to 1
    confidence: float
    markers_found: list[str]

class EmotionalClassifier:
    """
    Classify text as informative (factual) or emotional (hype).
    
    Uses a combination of:
    1. Emoji detection
    2. Exclamation/capitalization patterns
    3. Financial terminology density
    4. Hype phrase detection
    """
    
    # Emotional markers
    EMOTIONAL_PATTERNS = [
        r'🚀|🌙|💎|🙌|📈|📉|🔥|💰|🤑',  # Emojis
        r'to the moon',
        r'diamond hands',
        r'paper hands',
        r'hodl|hold the line',
        r'apes? together',
        r'tendies',
        r'yolo',
        r'let\'s go+',
        r'!!+',  # Multiple exclamation marks
    ]
    
    # Informative markers
    INFORMATIVE_PATTERNS = [
        r'reported|announced|released',
        r'revenue|earnings|profit|loss',
        r'billion|million|\$[\d,]+',
        r'quarter|fiscal|annual',
        r'CEO|CFO|executive',
        r'according to|sources say',
        r'percent|%',
        r'growth|decline|increase|decrease',
        r'market cap|valuation',
        r'analyst|forecast|estimate',
    ]
    
    def __init__(self, emotional_threshold: float = 0.6):
        self.emotional_threshold = emotional_threshold
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.emotional_regex = [
            re.compile(p, re.IGNORECASE) for p in self.EMOTIONAL_PATTERNS
        ]
        self.informative_regex = [
            re.compile(p, re.IGNORECASE) for p in self.INFORMATIVE_PATTERNS
        ]
    
    def classify(self, text: str) -> ClassificationResult:
        """Classify a single text."""
        
        # Count pattern matches
        emotional_matches = []
        informative_matches = []
        
        for pattern in self.emotional_regex:
            matches = pattern.findall(text)
            emotional_matches.extend(matches)
        
        for pattern in self.informative_regex:
            matches = pattern.findall(text)
            informative_matches.extend(matches)
        
        # Additional heuristics
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        exclaim_count = text.count('!')
        
        # Calculate scores
        text_length = len(text.split())
        emotional_density = len(emotional_matches) / max(text_length / 10, 1)
        informative_density = len(informative_matches) / max(text_length / 10, 1)
        
        # Adjust for caps and exclamation
        if caps_ratio > 0.3:
            emotional_density += 0.2
        if exclaim_count > 2:
            emotional_density += 0.1 * min(exclaim_count, 5)
        
        # Normalize
        emotional_score = min(emotional_density, 1.0)
        informative_score = min(informative_density, 1.0)
        
        # Determine type
        if emotional_score > self.emotional_threshold and informative_score < 0.3:
            content_type = ContentType.EMOTIONAL
        elif informative_score > 0.4 and emotional_score < 0.3:
            content_type = ContentType.INFORMATIVE
        else:
            content_type = ContentType.MIXED
        
        confidence = abs(emotional_score - informative_score)
        
        return ClassificationResult(
            content_type=content_type,
            informative_score=round(informative_score, 3),
            emotional_score=round(emotional_score, 3),
            confidence=round(confidence, 3),
            markers_found=emotional_matches + informative_matches
        )
    
    def classify_batch(self, texts: list[str]) -> list[ClassificationResult]:
        """Classify multiple texts."""
        return [self.classify(text) for text in texts]
    
    def get_aggregate_ratio(
        self, 
        results: list[ClassificationResult]
    ) -> dict:
        """Get aggregate statistics for a collection."""
        
        if not results:
            return {"informative_pct": 0, "emotional_pct": 0, "mixed_pct": 0}
        
        counts = {ct: 0 for ct in ContentType}
        for r in results:
            counts[r.content_type] += 1
        
        total = len(results)
        return {
            "informative_pct": round(counts[ContentType.INFORMATIVE] / total * 100, 1),
            "emotional_pct": round(counts[ContentType.EMOTIONAL] / total * 100, 1),
            "mixed_pct": round(counts[ContentType.MIXED] / total * 100, 1),
            "total_analyzed": total
        }
```

#### UI Integration

```
┌─────────────────────────────────────────────────────────────────┐
│  AAPL News Quality Analysis                                     │
│                                                                  │
│  📊 Content Type Distribution:                                   │
│  ██████████████████░░░░░░░░░░ Informative: 65%                  │
│  ████████░░░░░░░░░░░░░░░░░░░░ Emotional: 27%                    │
│  ███░░░░░░░░░░░░░░░░░░░░░░░░░ Mixed: 8%                         │
│                                                                  │
│  ⚠️ Insight: High informative ratio suggests news-driven        │
│     sentiment (more reliable signal)                             │
│                                                                  │
│  📰 Sample Informative:                                          │
│  "Apple reports Q1 revenue of $119B, beating estimates"         │
│                                                                  │
│  🎉 Sample Emotional:                                            │
│  "AAPL to the moon! 🚀🚀 Diamond hands!! 💎🙌"                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Database Schema Addition

```sql
ALTER TABLE fact_sentiment ADD COLUMN IF NOT EXISTS (
    informative_ratio DECIMAL(4,3),
    emotional_ratio DECIMAL(4,3),
    content_quality_flag VARCHAR(20)  -- 'HIGH', 'MEDIUM', 'LOW'
);
```

---

### B2: Historical Sentiment vs Price Chart

**Priority:** High  
**Estimated Effort:** 3 days  
**Dependencies:** 18 months of sentiment data collected

#### Description
Overlay historical sentiment scores with actual price movements to show correlation (or lack thereof). This visualization helps validate the approach and provides transparency.

#### Technical Implementation

```python
# src/features/correlation_analyzer.py

import pandas as pd
import numpy as np
from scipy import stats

class SentimentPriceCorrelation:
    """
    Analyze correlation between sentiment and price movements.
    """
    
    def __init__(self, lag_days: list[int] = [0, 1, 2, 3, 5]):
        self.lag_days = lag_days
    
    def calculate_correlation(
        self,
        sentiment_df: pd.DataFrame,  # columns: date, sentiment_score
        price_df: pd.DataFrame        # columns: date, return
    ) -> dict:
        """
        Calculate correlation between sentiment and returns at various lags.
        """
        # Merge on date
        merged = pd.merge(
            sentiment_df, 
            price_df, 
            on='date',
            how='inner'
        )
        
        results = {
            "correlations": {},
            "best_lag": None,
            "best_correlation": 0
        }
        
        for lag in self.lag_days:
            if lag > 0:
                # Shift returns to align with past sentiment
                merged[f'return_lag_{lag}'] = merged['return'].shift(-lag)
                corr_col = f'return_lag_{lag}'
            else:
                corr_col = 'return'
            
            # Calculate Pearson correlation
            valid_data = merged.dropna(subset=['sentiment_score', corr_col])
            
            if len(valid_data) > 10:
                corr, p_value = stats.pearsonr(
                    valid_data['sentiment_score'],
                    valid_data[corr_col]
                )
                
                results["correlations"][lag] = {
                    "correlation": round(corr, 4),
                    "p_value": round(p_value, 4),
                    "significant": p_value < 0.05,
                    "sample_size": len(valid_data)
                }
                
                if abs(corr) > abs(results["best_correlation"]):
                    results["best_correlation"] = corr
                    results["best_lag"] = lag
        
        return results
    
    def generate_chart_data(
        self,
        sentiment_df: pd.DataFrame,
        price_df: pd.DataFrame
    ) -> dict:
        """
        Generate data for overlaid chart visualization.
        """
        merged = pd.merge(
            sentiment_df,
            price_df,
            on='date',
            how='inner'
        ).sort_values('date')
        
        # Normalize both series to 0-100 for visual comparison
        merged['sentiment_normalized'] = (
            (merged['sentiment_score'] + 1) / 2 * 100
        )
        
        # Normalize price to percentage change from start
        start_price = merged['close'].iloc[0]
        merged['price_normalized'] = (
            (merged['close'] / start_price - 1) * 100 + 50
        )
        
        return {
            "dates": merged['date'].dt.strftime('%Y-%m-%d').tolist(),
            "sentiment": merged['sentiment_normalized'].round(2).tolist(),
            "price": merged['price_normalized'].round(2).tolist(),
            "correlation_stats": self.calculate_correlation(
                sentiment_df, price_df
            )
        }
```

#### API Endpoint

```python
# src/api/routers/stocks.py

@router.get("/stocks/{ticker}/correlation")
async def get_sentiment_price_correlation(
    ticker: str,
    days: int = 180
) -> CorrelationResponse:
    """
    Get historical sentiment vs price correlation data.
    """
    sentiment_data = await repository.get_sentiment_history(ticker, days)
    price_data = await repository.get_price_history(ticker, days)
    
    analyzer = SentimentPriceCorrelation()
    chart_data = analyzer.generate_chart_data(sentiment_data, price_data)
    
    return CorrelationResponse(
        ticker=ticker,
        period_days=days,
        chart_data=chart_data,
        correlation=chart_data["correlation_stats"]["best_correlation"],
        best_lag_days=chart_data["correlation_stats"]["best_lag"],
        interpretation=get_correlation_interpretation(
            chart_data["correlation_stats"]["best_correlation"]
        )
    )

def get_correlation_interpretation(corr: float) -> str:
    """Human-readable interpretation of correlation."""
    if corr > 0.5:
        return "Strong positive correlation - sentiment tends to lead price moves"
    elif corr > 0.2:
        return "Moderate positive correlation - some predictive signal"
    elif corr > -0.2:
        return "Weak correlation - sentiment and price move independently"
    elif corr > -0.5:
        return "Moderate negative correlation - contrarian signal"
    else:
        return "Strong negative correlation - sentiment inversely related"
```

#### UI Component (Streamlit)

```python
# src/dashboard/components/correlation_chart.py

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_correlation_chart(data: dict, ticker: str):
    """Render sentiment vs price correlation chart."""
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Sentiment line
    fig.add_trace(
        go.Scatter(
            x=data["dates"],
            y=data["sentiment"],
            name="Sentiment Score",
            line=dict(color="#00D4AA", width=2),
            hovertemplate="Sentiment: %{y:.1f}<br>Date: %{x}"
        ),
        secondary_y=False
    )
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=data["dates"],
            y=data["price"],
            name="Price (Normalized)",
            line=dict(color="#6366F1", width=2),
            hovertemplate="Price: %{y:.1f}<br>Date: %{x}"
        ),
        secondary_y=True
    )
    
    # Layout
    fig.update_layout(
        title=f"{ticker}: Sentiment vs Price (18 Months)",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_yaxes(title_text="Sentiment Score", secondary_y=False)
    fig.update_yaxes(title_text="Price Change %", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation stats
    stats = data["correlation_stats"]
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Correlation",
            f"{stats['best_correlation']:.2f}",
            help="Pearson correlation between sentiment and returns"
        )
    
    with col2:
        st.metric(
            "Best Lag",
            f"{stats['best_lag']} days",
            help="Sentiment leads price by this many days"
        )
    
    with col3:
        st.metric(
            "Sample Size",
            f"{stats['correlations'][stats['best_lag']]['sample_size']} days"
        )
```

---

### B3: Backtesting Results Display

**Priority:** Critical  
**Estimated Effort:** 4-5 days  
**Dependencies:** 18 months historical data, XGBoost model

#### Description
Show how Sen2Nal would have performed if signals were followed historically. This is critical for credibility and the research paper.

#### Technical Implementation

```python
# src/models/backtester.py

from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

@dataclass
class BacktestConfig:
    signal_threshold: float = 0.60  # Minimum score to trigger trade
    holding_period_days: int = 5    # Monday to Friday
    initial_capital: float = 10000
    position_size: float = 0.33     # 33% per stock (max 3 positions)
    commission: float = 0.001       # 0.1% per trade

@dataclass
class TradeResult:
    entry_date: datetime
    exit_date: datetime
    ticker: str
    entry_price: float
    exit_price: float
    signal_score: float
    return_pct: float
    correct_direction: bool

@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return_pct: float
    avg_return_per_trade: float
    max_drawdown_pct: float
    sharpe_ratio: float
    trades: list[TradeResult]
    equity_curve: list[dict]
    performance_by_signal: dict
    performance_by_market: dict

class SentimentBacktester:
    """
    Backtest sentiment-based trading strategy.
    
    Strategy:
    - Every Monday, select top 3 stocks with combined_score > threshold
    - Hold until Friday close
    - Calculate returns
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
    
    def run_backtest(
        self,
        sentiment_history: pd.DataFrame,  # date, ticker, combined_score, signal
        price_history: pd.DataFrame        # date, ticker, open, close
    ) -> BacktestResult:
        """
        Run backtest over historical data.
        """
        trades = []
        equity = [{"date": None, "value": self.config.initial_capital}]
        current_capital = self.config.initial_capital
        
        # Get all Mondays in the data
        sentiment_history['date'] = pd.to_datetime(sentiment_history['date'])
        mondays = sentiment_history[
            sentiment_history['date'].dt.dayofweek == 0
        ]['date'].unique()
        
        for monday in sorted(mondays):
            friday = monday + timedelta(days=4)
            
            # Get signals for this Monday
            monday_signals = sentiment_history[
                (sentiment_history['date'] == monday) &
                (sentiment_history['combined_score'] >= self.config.signal_threshold)
            ].nlargest(3, 'combined_score')
            
            if len(monday_signals) == 0:
                continue
            
            # Execute trades
            for _, row in monday_signals.iterrows():
                ticker = row['ticker']
                
                # Get prices
                monday_price = price_history[
                    (price_history['date'] == monday) &
                    (price_history['ticker'] == ticker)
                ]
                friday_price = price_history[
                    (price_history['date'] == friday) &
                    (price_history['ticker'] == ticker)
                ]
                
                if monday_price.empty or friday_price.empty:
                    continue
                
                entry = monday_price['open'].iloc[0]
                exit = friday_price['close'].iloc[0]
                
                # Calculate return
                gross_return = (exit - entry) / entry
                net_return = gross_return - (2 * self.config.commission)
                
                position_value = current_capital * self.config.position_size
                pnl = position_value * net_return
                
                trades.append(TradeResult(
                    entry_date=monday,
                    exit_date=friday,
                    ticker=ticker,
                    entry_price=entry,
                    exit_price=exit,
                    signal_score=row['combined_score'],
                    return_pct=round(net_return * 100, 2),
                    correct_direction=(net_return > 0) == (row['combined_score'] > 0.5)
                ))
            
            # Update capital
            weekly_pnl = sum(
                t.return_pct / 100 * current_capital * self.config.position_size
                for t in trades[-len(monday_signals):]
            )
            current_capital += weekly_pnl
            
            equity.append({
                "date": friday.strftime('%Y-%m-%d'),
                "value": round(current_capital, 2)
            })
        
        # Calculate metrics
        return self._calculate_metrics(trades, equity)
    
    def _calculate_metrics(
        self, 
        trades: list[TradeResult],
        equity: list[dict]
    ) -> BacktestResult:
        """Calculate backtest performance metrics."""
        
        if not trades:
            return BacktestResult(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, total_return_pct=0, avg_return_per_trade=0,
                max_drawdown_pct=0, sharpe_ratio=0, trades=[],
                equity_curve=equity, performance_by_signal={},
                performance_by_market={}
            )
        
        returns = [t.return_pct for t in trades]
        winning = [t for t in trades if t.return_pct > 0]
        losing = [t for t in trades if t.return_pct <= 0]
        
        # Max drawdown
        equity_values = [e['value'] for e in equity if e['date']]
        peak = equity_values[0]
        max_dd = 0
        for val in equity_values:
            if val > peak:
                peak = val
            dd = (peak - val) / peak
            max_dd = max(max_dd, dd)
        
        # Sharpe ratio (annualized, assuming weekly returns)
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (avg_return / std_return) * np.sqrt(52) if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Performance by signal strength
        strong_buy_trades = [t for t in trades if t.signal_score >= 0.70]
        buy_trades = [t for t in trades if 0.55 <= t.signal_score < 0.70]
        
        performance_by_signal = {
            "STRONG_BUY": {
                "count": len(strong_buy_trades),
                "avg_return": round(np.mean([t.return_pct for t in strong_buy_trades]) if strong_buy_trades else 0, 2),
                "win_rate": round(len([t for t in strong_buy_trades if t.return_pct > 0]) / max(len(strong_buy_trades), 1), 2)
            },
            "BUY": {
                "count": len(buy_trades),
                "avg_return": round(np.mean([t.return_pct for t in buy_trades]) if buy_trades else 0, 2),
                "win_rate": round(len([t for t in buy_trades if t.return_pct > 0]) / max(len(buy_trades), 1), 2)
            }
        }
        
        total_return = (equity_values[-1] - equity_values[0]) / equity_values[0] * 100
        
        return BacktestResult(
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=round(len(winning) / len(trades), 2),
            total_return_pct=round(total_return, 2),
            avg_return_per_trade=round(np.mean(returns), 2),
            max_drawdown_pct=round(max_dd * 100, 2),
            sharpe_ratio=round(sharpe, 2),
            trades=trades,
            equity_curve=equity,
            performance_by_signal=performance_by_signal,
            performance_by_market={}  # TODO: Add bull/bear market analysis
        )
```

#### UI Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 SEN2NAL BACKTEST RESULTS (18 Months)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SUMMARY METRICS                                                             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐    │
│  │ Total Return│ Win Rate    │ Trades      │ Max Drawdown│ Sharpe      │    │
│  │ +47.3%      │ 58%         │ 312         │ -12.4%      │ 1.24        │    │
│  └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘    │
│                                                                              │
│  EQUITY CURVE                                                                │
│  $15,000 ─────────────────────────────────────────────────────●             │
│  $12,500 ─────────────────────────────●───────────────────────              │
│  $10,000 ●────────────────────────────                                       │
│           Jan       Apr       Jul       Oct       Jan                        │
│                                                                              │
│  PERFORMANCE BY SIGNAL TYPE                                                  │
│  ┌──────────────┬─────────┬────────────┬──────────┐                         │
│  │ Signal       │ Trades  │ Avg Return │ Win Rate │                         │
│  ├──────────────┼─────────┼────────────┼──────────┤                         │
│  │ Strong Buy   │ 89      │ +1.8%      │ 68%      │ ← Best performer        │
│  │ Buy          │ 156     │ +0.9%      │ 55%      │                         │
│  │ Hold         │ 67      │ +0.2%      │ 51%      │                         │
│  └──────────────┴─────────┴────────────┴──────────┘                         │
│                                                                              │
│  ⚠️ DISCLAIMER: Past performance does not guarantee future results          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### B4: News Highlights with Sentiment Labels

**Priority:** High  
**Estimated Effort:** 2-3 days  
**Dependencies:** News ingestion pipeline

#### Description
Show actual news snippets with their individual sentiment contribution, so users can see exactly what's driving the score.

#### Implementation

```python
# src/api/schemas.py

class NewsHighlight(BaseModel):
    headline: str
    source: str
    published_at: datetime
    sentiment_score: float
    sentiment_contribution: float  # How much this article affected overall
    url: str | None

class NewsHighlightsResponse(BaseModel):
    ticker: str
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    highlights: list[NewsHighlight]  # Top 5 most impactful
```

```python
# src/features/news_highlighter.py

class NewsHighlighter:
    """
    Select and rank news articles by sentiment impact.
    """
    
    def get_top_highlights(
        self,
        articles: list[dict],
        max_highlights: int = 5
    ) -> list[dict]:
        """
        Get the most impactful news articles.
        
        Ranking factors:
        - Absolute sentiment score (extreme = more impactful)
        - Recency (newer = more relevant)
        - Source credibility weight
        """
        SOURCE_WEIGHTS = {
            "reuters": 1.5,
            "bloomberg": 1.5,
            "wsj": 1.4,
            "cnbc": 1.2,
            "yahoo": 1.0,
            "reddit": 0.8,
        }
        
        scored_articles = []
        
        for article in articles:
            # Calculate impact score
            sentiment_impact = abs(article['sentiment_score'])
            source_weight = SOURCE_WEIGHTS.get(
                article['source'].lower(), 1.0
            )
            
            # Recency decay (articles older than 24h get lower weight)
            hours_old = (datetime.now() - article['published_at']).total_seconds() / 3600
            recency_weight = max(0.5, 1 - (hours_old / 48))
            
            impact_score = sentiment_impact * source_weight * recency_weight
            
            scored_articles.append({
                **article,
                "impact_score": impact_score
            })
        
        # Sort by impact and return top N
        scored_articles.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return scored_articles[:max_highlights]
```

#### UI Component

```python
# src/dashboard/components/news_highlights.py

def render_news_highlights(highlights: list[dict]):
    st.subheader("📰 Key News Driving Sentiment")
    
    for article in highlights:
        score = article['sentiment_score']
        
        # Color and emoji based on sentiment
        if score > 0.3:
            color = "green"
            emoji = "🟢"
            contribution = f"+{article['sentiment_contribution']:.2f}"
        elif score < -0.3:
            color = "red"
            emoji = "🔴"
            contribution = f"{article['sentiment_contribution']:.2f}"
        else:
            color = "gray"
            emoji = "⚪"
            contribution = f"{article['sentiment_contribution']:.2f}"
        
        st.markdown(f"""
        {emoji} **{contribution}** [{article['headline']}]({article['url']})  
        *{article['source']} • {article['published_at'].strftime('%b %d, %H:%M')}*
        """)
```

---

## Category C Features

### C1: Email Alerts for Signal Changes

**Priority:** Low  
**Estimated Effort:** 3-4 days  
**Dependencies:** AWS SES or similar email service

#### Description
Notify users when a stock's signal changes significantly (e.g., from HOLD to BUY, or when conflict appears).

#### Implementation Overview

```python
# src/notifications/email_alerts.py

from dataclasses import dataclass
from enum import Enum
import boto3

class AlertType(Enum):
    SIGNAL_UPGRADE = "signal_upgrade"      # HOLD → BUY or BUY → STRONG_BUY
    SIGNAL_DOWNGRADE = "signal_downgrade"  # Opposite
    NEW_CONFLICT = "new_conflict"          # Conflict detected
    CONFLICT_RESOLVED = "conflict_resolved"

@dataclass
class AlertConfig:
    user_email: str
    watched_tickers: list[str]
    alert_types: list[AlertType]
    min_score_change: float = 0.10

class AlertService:
    def __init__(self):
        self.ses_client = boto3.client('ses')
    
    def check_and_send_alerts(
        self,
        today_sentiment: dict,
        yesterday_sentiment: dict,
        user_configs: list[AlertConfig]
    ):
        """Check for alert conditions and send notifications."""
        
        for config in user_configs:
            alerts_to_send = []
            
            for ticker in config.watched_tickers:
                today = today_sentiment.get(ticker)
                yesterday = yesterday_sentiment.get(ticker)
                
                if not today or not yesterday:
                    continue
                
                # Check signal change
                if today['signal'] != yesterday['signal']:
                    # Determine if upgrade or downgrade
                    signal_order = ['AVOID', 'HOLD', 'BUY', 'STRONG_BUY']
                    today_idx = signal_order.index(today['signal'])
                    yesterday_idx = signal_order.index(yesterday['signal'])
                    
                    if today_idx > yesterday_idx:
                        alert_type = AlertType.SIGNAL_UPGRADE
                    else:
                        alert_type = AlertType.SIGNAL_DOWNGRADE
                    
                    if alert_type in config.alert_types:
                        alerts_to_send.append({
                            "type": alert_type,
                            "ticker": ticker,
                            "old_signal": yesterday['signal'],
                            "new_signal": today['signal'],
                            "score": today['combined_score']
                        })
                
                # Check conflict changes
                if today.get('conflict_flag') and not yesterday.get('conflict_flag'):
                    if AlertType.NEW_CONFLICT in config.alert_types:
                        alerts_to_send.append({
                            "type": AlertType.NEW_CONFLICT,
                            "ticker": ticker,
                            "reason": today.get('conflict_reason')
                        })
            
            if alerts_to_send:
                self._send_email(config.user_email, alerts_to_send)
    
    def _send_email(self, email: str, alerts: list[dict]):
        """Send alert email via SES."""
        # Implementation with SES
        pass
```

#### Database Schema

```sql
CREATE TABLE user_alerts (
    alert_id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    watched_tickers TEXT[],  -- Array of tickers
    alert_types TEXT[],      -- Array of alert type strings
    min_score_change DECIMAL(4,2) DEFAULT 0.10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert_history (
    history_id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50),
    ticker VARCHAR(10),
    message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### C2: Prompt Engineering Transparency for LLM Comparison

**Priority:** Medium  
**Estimated Effort:** Documentation only (1 day)

#### Description
In the research page, show the exact prompts used for ChatGPT/Gemini/Grok to make the experiment reproducible and scientifically rigorous.

#### Implementation

```python
# src/constants.py

LLM_PROMPTS = {
    "standard_weekly": """
You are a financial analyst with expertise in U.S. equities. 
Based on current market conditions as of {date}, select exactly 3 S&P 500 
stocks that you believe will perform best over the next 5 trading days 
(Monday market open to Friday market close).

Consider the following factors in your analysis:
1. Recent news sentiment and media coverage
2. Technical indicators and price momentum
3. Seasonal patterns and calendar effects
4. Overall market conditions and sector trends
5. Fundamental factors if relevant

Respond with exactly 3 ticker symbols and a brief (1-2 sentence) reasoning 
for each selection.

Format your response as:
1. [TICKER]: [Brief reasoning]
2. [TICKER]: [Brief reasoning]
3. [TICKER]: [Brief reasoning]

Important: Only select from S&P 500 constituents. Focus on stocks with 
potential for short-term (1 week) gains.
""",
    
    "version_history": [
        {
            "version": "1.0",
            "active_from": "2026-01-06",
            "changes": "Initial prompt version"
        }
    ]
}
```

#### UI Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🤖 LLM PROMPT TRANSPARENCY                                                 │
│                                                                              │
│  The same prompt is used for all three LLMs to ensure fair comparison:      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PROMPT v1.0 (Used since Week 1)                                    │    │
│  │  ─────────────────────────────────────────────────────────────────  │    │
│  │                                                                      │    │
│  │  You are a financial analyst with expertise in U.S. equities.       │    │
│  │  Based on current market conditions as of [DATE], select exactly    │    │
│  │  3 S&P 500 stocks that you believe will perform best over the      │    │
│  │  next 5 trading days...                                             │    │
│  │                                                                      │    │
│  │  [Show Full Prompt ▼]                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  📋 Methodology Notes:                                                       │
│  • Prompts sent at 6:30 AM EST each Monday                                  │
│  • Temperature set to 0.7 for all models                                    │
│  • No additional context or follow-up questions                             │
│  • Raw responses logged for reproducibility                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### C3: Confidence Intervals on Predictions

**Priority:** Medium  
**Estimated Effort:** 2 days

#### Description
Don't just say "Bullish" - provide confidence intervals and uncertainty quantification to help users understand prediction reliability.

#### Implementation

```python
# src/features/confidence.py

from dataclasses import dataclass

@dataclass
class ConfidenceBreakdown:
    base_confidence: float
    adjustments: list[dict]  # {"factor": str, "adjustment": float}
    final_confidence: float
    interpretation: str

class ConfidenceCalculator:
    """
    Calculate and explain prediction confidence.
    """
    
    def calculate(
        self,
        nlp_confidence: float,      # From FinBERT
        article_count: int,
        source_agreement: float,    # How much sources agree
        conflict_flag: bool,
        score_boundary_distance: float  # Distance to nearest threshold
    ) -> ConfidenceBreakdown:
        """
        Calculate overall confidence with breakdown.
        """
        adjustments = []
        confidence = nlp_confidence
        
        # Article volume adjustment
        if article_count < 5:
            adj = -0.15
            adjustments.append({
                "factor": "Low article volume",
                "adjustment": adj,
                "explanation": f"Only {article_count} articles analyzed"
            })
            confidence += adj
        elif article_count > 20:
            adj = 0.10
            adjustments.append({
                "factor": "High article volume",
                "adjustment": adj,
                "explanation": f"{article_count} articles provide strong signal"
            })
            confidence += adj
        
        # Source agreement adjustment
        if source_agreement < 0.5:
            adj = -0.10
            adjustments.append({
                "factor": "Source disagreement",
                "adjustment": adj,
                "explanation": "News and Reddit show different sentiment"
            })
            confidence += adj
        elif source_agreement > 0.8:
            adj = 0.08
            adjustments.append({
                "factor": "Strong source agreement",
                "adjustment": adj,
                "explanation": "All sources show similar sentiment"
            })
            confidence += adj
        
        # Conflict adjustment
        if conflict_flag:
            adj = -0.15
            adjustments.append({
                "factor": "NLP-Calendar conflict",
                "adjustment": adj,
                "explanation": "Sentiment and calendar patterns disagree"
            })
            confidence += adj
        
        # Boundary proximity adjustment
        if score_boundary_distance < 0.05:
            adj = -0.10
            adjustments.append({
                "factor": "Near signal boundary",
                "adjustment": adj,
                "explanation": "Score is close to threshold, could flip"
            })
            confidence += adj
        
        final_confidence = max(0.1, min(0.99, confidence))
        
        # Interpretation
        if final_confidence >= 0.75:
            interpretation = "High confidence - multiple factors align"
        elif final_confidence >= 0.55:
            interpretation = "Moderate confidence - some uncertainty present"
        else:
            interpretation = "Low confidence - interpret with caution"
        
        return ConfidenceBreakdown(
            base_confidence=nlp_confidence,
            adjustments=adjustments,
            final_confidence=round(final_confidence, 2),
            interpretation=interpretation
        )
```

#### UI Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AAPL Signal: BUY                                                            │
│  Confidence: 73%                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━ │
│  Low                          Moderate                           High       │
│                                                                              │
│  📊 Confidence Breakdown:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Base (FinBERT)              0.78                                      │  │
│  │ + High article volume       +0.10  (34 articles analyzed)             │  │
│  │ + Strong source agreement   +0.08  (News & Reddit align)              │  │
│  │ - Near signal boundary      -0.10  (Score close to BUY/HOLD line)     │  │
│  │ - NLP-Calendar conflict     -0.13  (Calendar shows different signal)  │  │
│  │ ─────────────────────────────────────────────────────────────────────│  │
│  │ Final Confidence            0.73                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  💡 Moderate confidence - some uncertainty present                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority Matrix

| Feature | Effort | Impact | Priority Score | Recommended Order |
|---------|--------|--------|----------------|-------------------|
| B3: Backtesting Display | 5 days | Critical | 10 | 1st |
| B2: Correlation Chart | 3 days | High | 8 | 2nd |
| B4: News Highlights | 3 days | High | 8 | 3rd |
| B1: Emotional Classifier | 4 days | Medium | 6 | 4th |
| C2: Prompt Transparency | 1 day | Medium | 7 | 5th |
| C3: Confidence Intervals | 2 days | Medium | 6 | 6th |
| C1: Email Alerts | 4 days | Low | 4 | 7th |

---

---

### C4: Short-Term vs Long-Term Stock Classification

**Priority:** Medium  
**Estimated Effort:** 5-7 days  
**Dependencies:** Fundamental data integration, sector analysis

#### Description
Separate stocks into two categories based on investment horizon suitability:
1. **Short-term Trading Candidates** - Stocks with high sentiment volatility, momentum, and near-term catalysts
2. **Long-term Hold Candidates** - Stocks with strong fundamentals, growth potential (especially future tech-centric companies), and stable sentiment

This helps users understand which stocks are suitable for different investment strategies.

#### Rationale
Different stocks suit different investment approaches:
- **Short-term**: High-beta stocks, earnings plays, momentum stocks, meme stocks
- **Long-term**: Growth companies, emerging tech leaders, companies with strong moats

#### Technical Implementation

```python
# src/features/horizon_classifier.py

from dataclasses import dataclass
from enum import Enum
import numpy as np

class InvestmentHorizon(Enum):
    SHORT_TERM = "short_term"      # Days to weeks
    LONG_TERM = "long_term"        # Months to years
    MIXED = "mixed"                # Suitable for both

@dataclass
class HorizonFactors:
    # Short-term factors
    sentiment_volatility: float      # High = short-term
    momentum_strength: float         # High = short-term
    earnings_proximity: int          # Close = short-term
    news_frequency: float            # High = short-term
    reddit_mention_rate: float       # High = short-term (retail interest)
    
    # Long-term factors
    sector_growth_rate: float        # High = long-term
    is_tech_centric: bool            # True = long-term potential
    market_cap_stability: float      # High = long-term
    analyst_long_term_rating: float  # High = long-term
    innovation_score: float          # High = long-term (R&D, patents)

@dataclass
class HorizonClassification:
    horizon: InvestmentHorizon
    short_term_score: float          # 0 to 1
    long_term_score: float           # 0 to 1
    primary_factors: list[str]
    reasoning: str

class HorizonClassifier:
    """
    Classify stocks by suitable investment horizon.
    """
    
    # Sectors with high long-term growth potential
    GROWTH_SECTORS = [
        "Technology",
        "Healthcare", 
        "Communication Services"
    ]
    
    # Keywords indicating future tech focus
    TECH_KEYWORDS = [
        "AI", "artificial intelligence", "machine learning",
        "cloud", "SaaS", "autonomous", "electric vehicle",
        "semiconductor", "quantum", "biotech", "genomics",
        "renewable", "clean energy", "fintech", "blockchain"
    ]
    
    def __init__(
        self,
        short_term_threshold: float = 0.6,
        long_term_threshold: float = 0.6
    ):
        self.short_term_threshold = short_term_threshold
        self.long_term_threshold = long_term_threshold
    
    def classify(
        self,
        ticker: str,
        sentiment_history: list[float],      # Last 30 days
        price_history: list[float],          # Last 90 days
        news_count_daily: float,             # Avg news per day
        reddit_mentions_daily: float,        # Avg Reddit mentions
        sector: str,
        company_description: str,
        market_cap: float,
        days_to_earnings: int = None,
        analyst_rating: float = None         # 1-5 scale
    ) -> HorizonClassification:
        """
        Classify a stock's suitable investment horizon.
        """
        factors = []
        
        # Calculate short-term score
        short_term_score = 0.0
        
        # 1. Sentiment volatility (std dev of recent sentiment)
        if len(sentiment_history) > 5:
            sent_volatility = np.std(sentiment_history)
            if sent_volatility > 0.3:
                short_term_score += 0.25
                factors.append("High sentiment volatility")
        
        # 2. Price momentum
        if len(price_history) > 20:
            recent_return = (price_history[-1] - price_history[-20]) / price_history[-20]
            if abs(recent_return) > 0.10:  # >10% move in 20 days
                short_term_score += 0.20
                factors.append("Strong price momentum")
        
        # 3. Earnings proximity
        if days_to_earnings and days_to_earnings <= 14:
            short_term_score += 0.20
            factors.append(f"Earnings in {days_to_earnings} days")
        
        # 4. News frequency
        if news_count_daily > 5:
            short_term_score += 0.15
            factors.append("High news frequency")
        
        # 5. Reddit retail interest
        if reddit_mentions_daily > 10:
            short_term_score += 0.20
            factors.append("High retail interest (Reddit)")
        
        # Calculate long-term score
        long_term_score = 0.0
        
        # 1. Growth sector
        if sector in self.GROWTH_SECTORS:
            long_term_score += 0.20
            factors.append(f"Growth sector: {sector}")
        
        # 2. Tech-centric focus
        description_lower = company_description.lower()
        tech_matches = sum(
            1 for kw in self.TECH_KEYWORDS 
            if kw.lower() in description_lower
        )
        if tech_matches >= 2:
            long_term_score += 0.25
            factors.append("Future tech focus")
        
        # 3. Market cap stability (large caps more stable)
        if market_cap > 100_000_000_000:  # >$100B
            long_term_score += 0.15
            factors.append("Large cap stability")
        elif market_cap > 10_000_000_000:  # >$10B
            long_term_score += 0.10
        
        # 4. Analyst long-term rating
        if analyst_rating and analyst_rating >= 4.0:
            long_term_score += 0.20
            factors.append("Strong analyst rating")
        
        # 5. Low sentiment volatility (stable sentiment = long-term)
        if len(sentiment_history) > 5:
            sent_volatility = np.std(sentiment_history)
            if sent_volatility < 0.15:
                long_term_score += 0.20
                factors.append("Stable sentiment pattern")
        
        # Determine classification
        if short_term_score >= self.short_term_threshold and long_term_score < self.long_term_threshold:
            horizon = InvestmentHorizon.SHORT_TERM
            reasoning = "High volatility and momentum suggest short-term trading opportunities"
        elif long_term_score >= self.long_term_threshold and short_term_score < self.short_term_threshold:
            horizon = InvestmentHorizon.LONG_TERM
            reasoning = "Growth potential and stability suggest long-term holding"
        elif short_term_score >= self.short_term_threshold and long_term_score >= self.long_term_threshold:
            horizon = InvestmentHorizon.MIXED
            reasoning = "Suitable for both short-term trading and long-term investment"
        else:
            # Default based on higher score
            if short_term_score > long_term_score:
                horizon = InvestmentHorizon.SHORT_TERM
                reasoning = "Characteristics lean toward short-term opportunities"
            else:
                horizon = InvestmentHorizon.LONG_TERM
                reasoning = "Characteristics lean toward long-term potential"
        
        return HorizonClassification(
            horizon=horizon,
            short_term_score=round(short_term_score, 2),
            long_term_score=round(long_term_score, 2),
            primary_factors=factors,
            reasoning=reasoning
        )
```

#### Database Schema Addition

```sql
-- Add to fact_sentiment or create new table
CREATE TABLE fact_horizon_classification (
    classification_id   SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES dim_stocks(stock_id),
    date_id             INTEGER NOT NULL REFERENCES dim_calendar(date_id),
    
    horizon             VARCHAR(20) NOT NULL,  -- 'short_term', 'long_term', 'mixed'
    short_term_score    DECIMAL(4,3) NOT NULL,
    long_term_score     DECIMAL(4,3) NOT NULL,
    primary_factors     JSONB,
    reasoning           TEXT,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, date_id)
);

-- Index for filtering
CREATE INDEX idx_horizon_type ON fact_horizon_classification(horizon);
```

#### UI Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 INVESTMENT HORIZON ANALYSIS                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Short-Term Trading]  [Long-Term Holding]  [All Stocks]                    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔥 SHORT-TERM TRADING CANDIDATES                                           │
│  Stocks with high momentum, volatility, or near-term catalysts              │
│                                                                              │
│  ┌────────┬──────────────┬────────────┬────────────────────────────────┐    │
│  │ Ticker │ ST Score     │ Signal     │ Key Factors                     │    │
│  ├────────┼──────────────┼────────────┼────────────────────────────────┤    │
│  │ TSLA   │ 0.85 ██████  │ BUY        │ High volatility, retail buzz   │    │
│  │ NVDA   │ 0.78 █████   │ STRONG BUY │ Earnings in 7 days, momentum   │    │
│  │ AMD    │ 0.72 ████    │ BUY        │ Strong momentum, high news     │    │
│  └────────┴──────────────┴────────────┴────────────────────────────────┘    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  🌱 LONG-TERM HOLDING CANDIDATES                                            │
│  Future tech-centric companies with growth potential                        │
│                                                                              │
│  ┌────────┬──────────────┬────────────┬────────────────────────────────┐    │
│  │ Ticker │ LT Score     │ Signal     │ Key Factors                     │    │
│  ├────────┼──────────────┼────────────┼────────────────────────────────┤    │
│  │ MSFT   │ 0.88 ██████  │ BUY        │ AI leader, cloud growth, stable│    │
│  │ GOOGL  │ 0.82 █████   │ BUY        │ AI/ML focus, large cap stable  │    │
│  │ AMZN   │ 0.79 █████   │ HOLD       │ Cloud + AI, diversified tech   │    │
│  │ ASML   │ 0.76 ████    │ BUY        │ Semiconductor, future tech     │    │
│  └────────┴──────────────┴────────────┴────────────────────────────────┘    │
│                                                                              │
│  💡 Long-term candidates focus on:                                          │
│  • AI/ML and automation leaders                                             │
│  • Cloud computing and SaaS                                                 │
│  • Semiconductor and chip makers                                            │
│  • Clean energy and EVs                                                     │
│  • Biotech and genomics                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Stock Detail Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AAPL - Apple Inc.                                                          │
│                                                                              │
│  📊 INVESTMENT HORIZON                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  Classification: LONG-TERM HOLD 🌱                                    │  │
│  │                                                                        │  │
│  │  Short-Term Score: 0.35 ███░░░░░░░                                    │  │
│  │  Long-Term Score:  0.78 ███████░░░                                    │  │
│  │                                                                        │  │
│  │  Why Long-Term:                                                        │  │
│  │  • Technology sector with growth potential                            │  │
│  │  • AI and services expansion                                          │  │
│  │  • Large cap stability ($2.8T market cap)                            │  │
│  │  • Stable sentiment patterns                                          │  │
│  │                                                                        │  │
│  │  ⚠️ Note: This classification is for informational purposes only     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### API Endpoint

```python
@router.get("/stocks/{ticker}/horizon")
async def get_stock_horizon(ticker: str) -> HorizonResponse:
    """Get investment horizon classification for a stock."""
    pass

@router.get("/stocks/horizon/short-term")
async def get_short_term_candidates(limit: int = 10) -> list[StockHorizonSummary]:
    """Get top short-term trading candidates."""
    pass

@router.get("/stocks/horizon/long-term")
async def get_long_term_candidates(limit: int = 10) -> list[StockHorizonSummary]:
    """Get top long-term holding candidates."""
    pass
```

#### Future Tech Focus Criteria

For identifying "future tech-centric" companies suitable for long-term holding:

| Category | Keywords/Criteria | Examples |
|----------|-------------------|----------|
| AI/ML | "artificial intelligence", "machine learning", "neural network" | NVDA, GOOGL, MSFT |
| Cloud | "cloud computing", "SaaS", "infrastructure" | AMZN, CRM, SNOW |
| Semiconductor | "chip", "semiconductor", "processor" | ASML, TSM, AMD |
| Clean Energy | "renewable", "solar", "EV", "battery" | TSLA, ENPH, NEE |
| Biotech | "genomics", "gene therapy", "CRISPR" | ILMN, CRSP, MRNA |
| Fintech | "digital payments", "blockchain", "DeFi" | SQ, PYPL, V |
| Automation | "robotics", "autonomous", "industrial IoT" | ISRG, ROK, HON |

#### Implementation Notes

1. **Data Requirements:**
   - Company descriptions (from Yahoo Finance or SEC filings)
   - Analyst ratings (optional, from Alpha Vantage)
   - Historical price data (90 days minimum)
   - Sentiment history (30 days minimum)

2. **Update Frequency:**
   - Re-classify weekly (Sunday night)
   - Horizon changes slowly, no need for daily updates

3. **Disclaimer:**
   - Must include warning that this is not investment advice
   - Long-term candidates are speculative growth plays

---

## Version Roadmap

### Version 1.1 (Post-Experiment)
- B3: Backtesting Display
- B2: Correlation Chart
- C2: Prompt Transparency

### Version 1.2 (If Time Permits)
- B4: News Highlights
- C3: Confidence Intervals

### Version 2.0 (Future)
- B1: Emotional Classifier
- C1: Email Alerts
- **C4: Short-Term vs Long-Term Classification** ⭐ NEW
- Additional features based on user feedback

---

## Notes for Implementation

1. **Data Dependencies**: Features B2, B3 require 18 months of historical data. Start collecting immediately even if features are delayed.

2. **API Rate Limits**: B4 (News Highlights) increases API calls. Consider caching strategy.

3. **Testing Requirements**: Each feature should have unit tests before integration.

4. **Documentation**: Update API docs and user guide with each new feature.

5. **Performance**: B3 (Backtesting) can be computationally expensive. Consider pre-computing and caching results.

---

*This document will be updated as features are prioritized and implemented.*
