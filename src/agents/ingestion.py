"""AG-01: Data Ingestion Agent.

Fetches stock data from external APIs:
- Alpha Vantage / yfinance: OHLCV price data
- NewsAPI: Financial news headlines
- Reddit (PRAW): r/stocks, r/wallstreetbets posts
- CNN Fear & Greed index

Normalizes data, validates with contracts, stores in staging + fact tables.
"""

import hashlib
import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, cast

import requests  # type: ignore[import-untyped]
from sqlalchemy import select

from src.agents.base import BaseAgent
from src.config import settings
from src.constants import TOP_10_TICKERS
from src.database.models import (
    DimCalendar,
    DimFearGreed,
    DimStock,
    FactPrice,
    StgNewsRaw,
    StgRedditRaw,
)

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    """Fetches and stores raw data from external sources."""

    stage_name = "ingestion"

    @property
    def name(self) -> str:
        return "AG-01-Ingestion"

    def execute(self, target_date: date | None = None,
                tickers: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        target = target_date or date.today()
        ticker_list = tickers or list(TOP_10_TICKERS)
        self.logger.info(f"Ingesting data for {target} — {len(ticker_list)} tickers")

        results: dict[str, Any] = {"target_date": str(target), "tickers": ticker_list}

        # Ensure dim_stocks rows exist
        self._ensure_stocks(ticker_list)

        # Ensure dim_calendar row exists for target date
        self._ensure_calendar(target)

        # 1. Price data (yfinance — free, no key required)
        prices = self._ingest_prices(ticker_list, target)
        results["prices_ingested"] = prices

        # 2. News headlines (NewsAPI)
        news = self._ingest_news(ticker_list, target)
        results["news_ingested"] = news

        # 3. Reddit posts (PRAW or pushshift fallback)
        reddit = self._ingest_reddit(ticker_list)
        results["reddit_ingested"] = reddit

        # 4. Fear & Greed index
        fg = self._ingest_fear_greed(target)
        results["fear_greed"] = fg

        self.db.commit()
        return results

    # =========================================================================
    # Stock dimension management
    # =========================================================================

    def _ensure_stocks(self, tickers: list[str]) -> None:
        """Insert any missing tickers into dim_stocks."""
        existing = set(self.db.execute(select(DimStock.ticker)).scalars().all())
        missing = set(tickers) - existing
        if not missing:
            return

        stock_info = _get_stock_metadata(list(missing))
        for ticker, info in stock_info.items():
            self.db.add(DimStock(
                ticker=ticker,
                company_name=info.get("company_name", ticker),
                sector=info.get("sector", "Unknown"),
                industry=info.get("industry"),
                market_cap=info.get("market_cap"),
                sp500_rank=info.get("sp500_rank"),
                is_active=True,
            ))
        self.db.flush()
        self.logger.info(f"Added {len(missing)} stocks to dim_stocks")

    def _ensure_calendar(self, target: date) -> None:
        """Insert calendar row if missing for target date."""
        exists = self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == target)
        ).scalar()
        if exists:
            return

        is_weekend = target.weekday() >= 5
        self.db.add(DimCalendar(
            date=target,
            day_of_week=target.weekday(),
            day_of_week_name=target.strftime("%A"),
            day_of_month=target.day,
            week_of_year=target.isocalendar()[1],
            month=target.month,
            month_name=target.strftime("%B"),
            quarter=(target.month - 1) // 3 + 1,
            year=target.year,
            is_weekend=is_weekend,
            is_trading_day=not is_weekend,
            is_month_start=target.day == 1,
            is_month_end=(target + timedelta(days=1)).month != target.month,
            is_quarter_start=target.month in (1, 4, 7, 10) and target.day == 1,
            is_quarter_end=target.month in (3, 6, 9, 12)
                          and (target + timedelta(days=1)).month != target.month,
            is_year_start=target.month == 1 and target.day == 1,
            is_year_end=target.month == 12 and target.day == 31,
            is_us_holiday=False,
        ))
        self.db.flush()

    # =========================================================================
    # Price ingestion (yfinance)
    # =========================================================================

    def _ingest_prices(self, tickers: list[str], target: date) -> int:
        """Fetch OHLCV data via yfinance and store in fact_prices."""
        try:
            import yfinance as yf
        except ImportError:
            self.logger.warning("yfinance not installed — skipping price ingestion")
            return 0

        count = 0
        start = target - timedelta(days=5)
        end = target + timedelta(days=1)

        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=str(start), end=str(end))
                if hist.empty:
                    self.logger.debug(f"No price data for {ticker}")
                    continue

                stock_id = self._get_stock_id(ticker)
                if not stock_id:
                    continue

                for idx, row in hist.iterrows():
                    row_date = idx.date() if hasattr(idx, 'date') else idx
                    date_id = self._get_or_create_date_id(row_date)

                    existing = self.db.execute(
                        select(FactPrice.price_id).where(
                            FactPrice.stock_id == stock_id,
                            FactPrice.date_id == date_id,
                        )
                    ).scalar()
                    if existing:
                        continue

                    prev_close = hist["Close"].shift(1).get(idx)
                    daily_ret = ((row["Close"] - prev_close) / prev_close
                                 if prev_close and prev_close > 0 else None)

                    self.db.add(FactPrice(
                        stock_id=stock_id,
                        date_id=date_id,
                        date=row_date,
                        open=round(row["Open"], 4),
                        high=round(row["High"], 4),
                        low=round(row["Low"], 4),
                        close=round(row["Close"], 4),
                        adj_close=round(row["Close"], 4),
                        volume=int(row["Volume"]),
                        daily_return=round(daily_ret, 5) if daily_ret else None,
                        intraday_range=round((row["High"] - row["Low"]) / row["Open"], 5)
                        if row["Open"] > 0 else None,
                    ))
                    count += 1

                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                self.logger.warning(f"Price fetch failed for {ticker}: {e}")

        self.db.flush()
        self.logger.info(f"Ingested {count} price records")
        return count

    # =========================================================================
    # News ingestion (NewsAPI)
    # =========================================================================

    def _ingest_news(self, tickers: list[str], target: date) -> int:
        """Fetch financial news from NewsAPI and store in stg_news_raw."""
        api_key = settings.newsapi_api_key
        if not api_key:
            self.logger.info("No NewsAPI key configured — skipping news ingestion")
            return 0

        count = 0
        from_date = (target - timedelta(days=3)).isoformat()
        to_date = target.isoformat()

        for ticker in tickers:
            try:
                resp = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": f'"{ticker}" stock',
                        "from": from_date,
                        "to": to_date,
                        "language": "en",
                        "sortBy": "relevancy",
                        "pageSize": 10,
                        "apiKey": api_key,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                articles = resp.json().get("articles", [])

                for article in articles:
                    headline = article.get("title", "").strip()
                    if not headline:
                        continue

                    content_hash = hashlib.sha256(headline.encode()).hexdigest()

                    existing = self.db.execute(
                        select(StgNewsRaw.raw_id).where(
                            StgNewsRaw.content_hash == content_hash
                        )
                    ).scalar()
                    if existing:
                        continue

                    self.db.add(StgNewsRaw(
                        source="newsapi",
                        external_id=article.get("url", "")[:100],
                        headline=headline,
                        summary=article.get("description", "")[:500] if article.get("description") else None,
                        url=article.get("url"),
                        published_at=_parse_datetime(article.get("publishedAt")),
                        tickers_mentioned=[ticker],
                        content_hash=content_hash,
                        is_processed=False,
                        is_duplicate=False,
                    ))
                    count += 1

                time.sleep(1.0)  # NewsAPI rate limiting
            except Exception as e:
                self.logger.warning(f"NewsAPI fetch failed for {ticker}: {e}")

        self.db.flush()
        self.logger.info(f"Ingested {count} news articles")
        return count

    # =========================================================================
    # Reddit ingestion (PRAW)
    # =========================================================================

    def _ingest_reddit(self, tickers: list[str]) -> int:
        """Fetch Reddit posts from finance subreddits via PRAW."""
        client_id = settings.reddit_client_id
        client_secret = settings.reddit_client_secret
        if not client_id or not client_secret:
            self.logger.info("No Reddit credentials configured — skipping Reddit ingestion")
            return 0

        try:
            import praw
        except ImportError:
            self.logger.warning("praw not installed — skipping Reddit ingestion")
            return 0

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=settings.reddit_user_agent,
        )

        count = 0
        subreddits = ["stocks", "wallstreetbets", "investing"]
        ticker_set = set(t.upper() for t in tickers)

        for sub_name in subreddits:
            try:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.hot(limit=50):
                    # Check if post mentions any of our tickers
                    text = f"{post.title} {post.selftext}"
                    mentioned = [t for t in ticker_set if f"${t}" in text or f" {t} " in text]
                    if not mentioned:
                        continue

                    existing = self.db.execute(
                        select(StgRedditRaw.raw_id).where(
                            StgRedditRaw.subreddit == sub_name,
                            StgRedditRaw.post_id == post.id,
                        )
                    ).scalar()
                    if existing:
                        continue

                    self.db.add(StgRedditRaw(
                        subreddit=sub_name,
                        post_id=post.id,
                        post_type="submission",
                        title=post.title[:500] if post.title else None,
                        body=post.selftext[:2000] if post.selftext else None,
                        author=str(post.author)[:50] if post.author else None,
                        score=post.score,
                        num_comments=post.num_comments,
                        created_utc=datetime.utcfromtimestamp(post.created_utc),
                        tickers_mentioned=mentioned,
                        is_processed=False,
                    ))
                    count += 1

                time.sleep(0.5)
            except Exception as e:
                self.logger.warning(f"Reddit fetch failed for r/{sub_name}: {e}")

        self.db.flush()
        self.logger.info(f"Ingested {count} Reddit posts")
        return count

    # =========================================================================
    # Fear & Greed index
    # =========================================================================

    def _ingest_fear_greed(self, target: date) -> dict[str, Any] | None:
        """Fetch CNN Fear & Greed index."""
        try:
            resp = requests.get(
                "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                headers={"User-Agent": "Sen2Nal/1.0"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            score_data = data.get("fear_and_greed", {})
            score = int(score_data.get("score", 0))
            rating = score_data.get("rating", "Neutral")

            # Previous close
            prev = data.get("fear_and_greed_historical", {}).get("data", [])
            prev_score = int(prev[-2][1]) if len(prev) >= 2 else None

            date_id = self._get_or_create_date_id(target)

            existing = self.db.execute(
                select(DimFearGreed.fg_id).where(DimFearGreed.date == target)
            ).scalar()

            if not existing:
                self.db.add(DimFearGreed(
                    date_id=date_id,
                    date=target,
                    score=score,
                    classification=rating,
                    prev_score=prev_score,
                    score_change=score - prev_score if prev_score else None,
                ))
                self.db.flush()

            result = {"score": score, "classification": rating}
            self.logger.info(f"Fear & Greed: {score} ({rating})")
            return result

        except Exception as e:
            self.logger.warning(f"Fear & Greed fetch failed: {e}")
            return None

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_stock_id(self, ticker: str) -> int | None:
        return self.db.execute(
            select(DimStock.stock_id).where(DimStock.ticker == ticker)
        ).scalar()

    def _get_or_create_date_id(self, d: date) -> int:
        date_id = self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == d)
        ).scalar()
        if date_id:
            return date_id
        self._ensure_calendar(d)
        return cast(int, self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == d)
        ).scalar())


# =============================================================================
# Module-level helpers
# =============================================================================

_STOCK_META: dict[str, dict[str, Any]] = {
    "AAPL": {"company_name": "Apple Inc.", "sector": "Technology", "sp500_rank": 1},
    "MSFT": {"company_name": "Microsoft Corp.", "sector": "Technology", "sp500_rank": 2},
    "GOOGL": {"company_name": "Alphabet Inc.", "sector": "Technology", "sp500_rank": 3},
    "AMZN": {"company_name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "sp500_rank": 4},
    "NVDA": {"company_name": "NVIDIA Corp.", "sector": "Technology", "sp500_rank": 5},
    "META": {"company_name": "Meta Platforms Inc.", "sector": "Communication Services", "sp500_rank": 6},
    "TSLA": {"company_name": "Tesla Inc.", "sector": "Consumer Discretionary", "sp500_rank": 7},
    "BRK.B": {"company_name": "Berkshire Hathaway Inc.", "sector": "Financials", "sp500_rank": 8},
    "JPM": {"company_name": "JPMorgan Chase & Co.", "sector": "Financials", "sp500_rank": 9},
    "V": {"company_name": "Visa Inc.", "sector": "Financials", "sp500_rank": 10},
}


def _get_stock_metadata(tickers: list[str]) -> dict[str, dict[str, Any]]:
    """Return metadata for given tickers. Falls back to yfinance if not in cache."""
    result = {}
    for ticker in tickers:
        if ticker in _STOCK_META:
            result[ticker] = _STOCK_META[ticker]
        else:
            try:
                import yfinance as yf
                info = yf.Ticker(ticker).info
                result[ticker] = {
                    "company_name": info.get("longName", ticker),
                    "sector": info.get("sector", "Unknown"),
                    "industry": info.get("industry"),
                    "market_cap": info.get("marketCap"),
                }
            except Exception:
                result[ticker] = {"company_name": ticker, "sector": "Unknown"}
    return result


def _parse_datetime(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
