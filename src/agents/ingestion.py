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
import math
import time
from datetime import date, datetime, timedelta, timezone
from numbers import Real
from typing import Any, cast

import requests  # type: ignore[import-untyped]
from sqlalchemy import select

from src.agents.base import BaseAgent
from src.config import settings
from src.constants import TOP_10_TICKERS
from src.contracts.base import DataContractViolation
from src.contracts.ingestion import FearGreedWrite, NewsWrite, PriceWrite, RedditWrite
from src.database.models import (
    DimCalendar,
    DimFearGreed,
    DimStock,
    FactPrice,
    StgNewsRaw,
    StgRedditRaw,
)
from src.data_quality.validator import require_record

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
        columns = ["Open", "High", "Low", "Close", "Volume"]

        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=str(start), end=str(end))
            except Exception:
                self.logger.warning("Price fetch failed for %s", ticker)
                continue
            if len(hist.index) == 0:
                self.logger.debug("No price data for %s", ticker)
                continue
            if not hist.columns.is_unique or any(column not in hist.columns for column in columns):
                raise _invalid_ingestion_field("price_columns")

            stock_id = self._get_stock_id(ticker)
            if stock_id is None:
                raise _invalid_ingestion_field("stock_id")

            prev_date = start - timedelta(days=1)
            prev_close: float | None = None
            bars = hist[columns]
            for idx, open_raw, high_raw, low_raw, close_raw, volume_raw in bars.itertuples(name=None):
                row_date = idx.date() if hasattr(idx, "date") else idx
                if not isinstance(row_date, date) or not prev_date < row_date <= target:
                    raise _invalid_ingestion_field("price_date")
                price_open = _source_number(open_raw, "open")
                high = _source_number(high_raw, "high")
                low = _source_number(low_raw, "low")
                close = _source_number(close_raw, "close")
                if price_open <= 0 or close <= 0:
                    raise _invalid_ingestion_field("price_bar")
                _source_number(volume_raw, "volume")
                volume = int(volume_raw)
                if volume_raw != volume:
                    raise _invalid_ingestion_field("volume")

                date_id = self._get_or_create_date_id(row_date)
                values = {
                    "stock_id": stock_id,
                    "date_id": date_id,
                    "date": row_date,
                    "open": round(price_open, 4),
                    "high": round(high, 4),
                    "low": round(low, 4),
                    "close": round(close, 4),
                    "adj_close": round(close, 4),
                    "volume": volume,
                    "daily_return": (round((close - prev_close) / prev_close, 5)
                                     if prev_close is not None else None),
                    "intraday_range": round((high - low) / price_open, 5),
                }
                require_record("ingestion", PriceWrite, values)
                prev_date, prev_close = row_date, close

                existing = self.db.execute(
                    select(FactPrice.price_id).where(
                        FactPrice.stock_id == stock_id,
                        FactPrice.date_id == date_id,
                    )
                ).scalar()
                if not existing:
                    self.db.add(FactPrice(**values))
                    count += 1

            time.sleep(0.2)  # Rate limiting

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
            except Exception:
                self.logger.warning("NewsAPI fetch failed for %s", ticker)
                continue

            try:
                payload = resp.json()
            except ValueError:
                raise _invalid_ingestion_field("articles") from None
            articles = payload.get("articles") if isinstance(payload, dict) else None
            if not isinstance(articles, list):
                raise _invalid_ingestion_field("articles")

            for article in articles:
                if not isinstance(article, dict):
                    raise _invalid_ingestion_field("article")
                headline = (_source_text(article.get("title"), "headline") or "").strip()
                if not headline:
                    continue

                content_hash = hashlib.sha256(headline.encode()).hexdigest()
                url = _source_text(article.get("url"), "url")
                values = {
                    "source": "newsapi",
                    "external_id": url[:100] if url else None,
                    "headline": headline,
                    "summary": _source_text(article.get("description"), "summary", 500),
                    "url": url,
                    "published_at": _parse_datetime(article.get("publishedAt")),
                    "tickers_mentioned": [ticker],
                    "content_hash": content_hash,
                    "is_processed": False,
                    "is_duplicate": False,
                }
                require_record("ingestion", NewsWrite, values)
                existing = self.db.execute(
                    select(StgNewsRaw.raw_id).where(StgNewsRaw.content_hash == content_hash)
                ).scalar()
                if not existing:
                    self.db.add(StgNewsRaw(**values))
                    count += 1

            time.sleep(1.0)  # NewsAPI rate limiting

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
                posts = list(reddit.subreddit(sub_name).hot(limit=50))
            except Exception:
                self.logger.warning("Reddit fetch failed for r/%s", sub_name)
                continue

            for post in posts:
                title = _source_text(getattr(post, "title", None), "title")
                body = _source_text(getattr(post, "selftext", None), "body")
                text = f"{title or ''} {body or ''}"
                mentioned = sorted(t for t in ticker_set if f"${t}" in text or f" {t} " in text)
                if not mentioned:
                    continue

                timestamp = getattr(post, "created_utc", None)
                if isinstance(timestamp, bool) or not isinstance(timestamp, (float, int)):
                    raise _invalid_ingestion_field("created_utc")
                try:
                    created_utc = datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None)
                except (OverflowError, OSError, ValueError):
                    raise _invalid_ingestion_field("created_utc") from None
                values = {
                    "subreddit": sub_name,
                    "post_id": getattr(post, "id", None),
                    "post_type": "submission",
                    "title": title[:500] if title else None,
                    "body": body[:2000] if body else None,
                    "author": str(post.author)[:50] if getattr(post, "author", None) else None,
                    "score": getattr(post, "score", None),
                    "num_comments": getattr(post, "num_comments", None),
                    "created_utc": created_utc,
                    "tickers_mentioned": mentioned,
                    "is_processed": False,
                }
                require_record("ingestion", RedditWrite, values)
                existing = self.db.execute(
                    select(StgRedditRaw.raw_id).where(
                        StgRedditRaw.subreddit == sub_name,
                        StgRedditRaw.post_id == post.id,
                    )
                ).scalar()
                if not existing:
                    self.db.add(StgRedditRaw(**values))
                    count += 1

            time.sleep(0.5)

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
        except Exception:
            self.logger.warning("Fear & Greed fetch failed")
            return None
        try:
            data = resp.json()
        except ValueError:
            raise _invalid_ingestion_field("fear_and_greed") from None
        score_data = data.get("fear_and_greed") if isinstance(data, dict) else None
        if not isinstance(score_data, dict):
            raise _invalid_ingestion_field("fear_and_greed")

        score = _index_score(score_data.get("score"), "score")
        rating = _source_text(score_data.get("rating"), "classification")
        history = data.get("fear_and_greed_historical", {})
        points = history.get("data", []) if isinstance(history, dict) else None
        if not isinstance(points, list):
            raise _invalid_ingestion_field("fear_and_greed_historical")
        prev_score = None
        if len(points) >= 2:
            point = points[-2]
            if isinstance(point, dict):
                prev_score = _index_score(point.get("y"), "prev_score")
            elif isinstance(point, list) and len(point) == 2:
                prev_score = _index_score(point[1], "prev_score")
            else:
                raise _invalid_ingestion_field("prev_score")

        values = {
            "date_id": self._get_or_create_date_id(target),
            "date": target,
            "score": score,
            "classification": rating.strip() if rating else None,
            "prev_score": prev_score,
            "score_change": score - prev_score if prev_score is not None else None,
        }
        require_record("ingestion", FearGreedWrite, values)
        existing = self.db.execute(
            select(DimFearGreed.fg_id).where(DimFearGreed.date == target)
        ).scalar()
        if not existing:
            self.db.add(DimFearGreed(**values))
            self.db.flush()

        self.logger.info("Fear & Greed score: %s", score)
        return {"score": score, "classification": values["classification"]}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_stock_id(self, ticker: str) -> int | None:
        return cast(int | None, self.db.execute(
            select(DimStock.stock_id).where(DimStock.ticker == ticker)
        ).scalar())

    def _get_or_create_date_id(self, d: date) -> int:
        date_id = cast(int | None, self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == d)
        ).scalar())
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


def _invalid_ingestion_field(field: str) -> DataContractViolation:
    return DataContractViolation("ingestion", [{"loc": (field,), "type": "invalid_source_field"}])


def _source_text(value: object, field: str, limit: int | None = None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or "\x00" in value:
        raise _invalid_ingestion_field(field)
    return value[:limit] or None


def _source_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise _invalid_ingestion_field(field)
    try:
        number = float(value)
    except OverflowError:
        raise _invalid_ingestion_field(field) from None
    if not math.isfinite(number):
        raise _invalid_ingestion_field(field)
    return number


def _index_score(value: object, field: str) -> int:
    number = _source_number(value, field)
    if not 0 <= number <= 100:
        raise _invalid_ingestion_field(field)
    return int(number)


def _parse_datetime(s: object) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        parsed = datetime.fromisoformat(s)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except (OverflowError, ValueError):
        return None
    return None
