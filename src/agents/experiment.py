"""AG-06: Experiment Tracker Agent.

Tracks the weekly AI vs AI experiment:
- SEN2NAL: picks based on pipeline signals
- ChatGPT, Gemini, Grok: picks from LLM API calls

Each week:
1. Monday: each method picks 3 stocks, record entry prices
2. Friday: record exit prices, compute returns
3. Determine weekly winner
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import select

from src.agents.base import BaseAgent
from src.config import settings
from src.constants import LLM_EXPERIMENT_PROMPT
from src.database.models import DimStock, FactExperiment, FactPrice, FactSentiment

logger = logging.getLogger(__name__)


class ExperimentAgent(BaseAgent):
    """Tracks weekly stock-picking experiment across SEN2NAL and LLMs."""

    @property
    def name(self) -> str:
        return "AG-06-Experiment"

    def execute(self, target_date: date | None = None, **kwargs: Any) -> dict[str, Any]:
        target = target_date or date.today()
        year = target.year
        week = target.isocalendar()[1]

        results: dict[str, Any] = {"year": year, "week": week}

        # Monday: generate picks
        if target.weekday() == 0:  # Monday
            results["action"] = "entry"
            results["picks"] = self._generate_all_picks(target, year, week)
        # Friday: close positions
        elif target.weekday() == 4:  # Friday
            results["action"] = "exit"
            results["exits"] = self._close_positions(target, year, week)
        else:
            results["action"] = "none"
            results["message"] = "Experiment runs Monday (entry) and Friday (exit) only"

        self.db.commit()
        return results

    # =========================================================================
    # Entry (Monday picks)
    # =========================================================================

    def _generate_all_picks(self, entry_date: date, year: int, week: int) -> dict:
        """Generate picks for all methods."""
        picks = {}

        # SEN2NAL picks: top 3 by combined_score
        picks["SEN2NAL"] = self._sen2nal_picks(entry_date, year, week)

        # LLM picks (if API keys configured)
        for method in ["CHATGPT", "GEMINI", "GROK"]:
            picks[method] = self._llm_picks(method, entry_date, year, week)

        return picks

    def _sen2nal_picks(self, entry_date: date, year: int, week: int) -> dict:
        """Pick top 3 stocks by Sen2Nal combined score."""
        # Check if already picked this week
        existing = self.db.execute(
            select(FactExperiment).where(
                FactExperiment.year == year,
                FactExperiment.week_number == week,
                FactExperiment.method == "SEN2NAL",
            )
        ).scalar()
        if existing:
            return {"status": "already_picked"}

        # Get top 3 by combined_score from latest sentiment
        top_stocks = self.db.execute(
            select(FactSentiment, DimStock).join(
                DimStock, FactSentiment.stock_id == DimStock.stock_id
            ).order_by(
                FactSentiment.date_id.desc(),
                FactSentiment.combined_score.desc(),
            ).limit(30)
        ).all()

        # Dedupe by ticker, take top 3
        seen = set()
        picks = []
        for sent, stock in top_stocks:
            if stock.ticker not in seen:
                seen.add(stock.ticker)
                picks.append((stock.ticker, float(sent.combined_score or 0)))
            if len(picks) >= 3:
                break

        if len(picks) < 3:
            # Fallback: use hardcoded top stocks
            from src.constants import TOP_10_TICKERS
            for t in TOP_10_TICKERS:
                if t not in seen:
                    picks.append((t, 0.5))
                    seen.add(t)
                if len(picks) >= 3:
                    break

        # Get entry prices
        entry_prices = {}
        for ticker, _ in picks:
            price = self._get_latest_price(ticker)
            entry_prices[ticker] = price

        # Record experiment
        self.db.add(FactExperiment(
            week_number=week,
            year=year,
            method="SEN2NAL",
            entry_date=entry_date,
            stock_1_ticker=picks[0][0],
            stock_1_score=Decimal(str(picks[0][1])),
            stock_1_entry=Decimal(str(entry_prices.get(picks[0][0], 0))),
            stock_2_ticker=picks[1][0],
            stock_2_score=Decimal(str(picks[1][1])),
            stock_2_entry=Decimal(str(entry_prices.get(picks[1][0], 0))),
            stock_3_ticker=picks[2][0],
            stock_3_score=Decimal(str(picks[2][1])),
            stock_3_entry=Decimal(str(entry_prices.get(picks[2][0], 0))),
        ))
        self.db.flush()

        return {
            "status": "picked",
            "stocks": [p[0] for p in picks],
            "scores": [p[1] for p in picks],
        }

    def _llm_picks(self, method: str, entry_date: date, year: int, week: int) -> dict:
        """Get stock picks from an LLM API."""
        existing = self.db.execute(
            select(FactExperiment).where(
                FactExperiment.year == year,
                FactExperiment.week_number == week,
                FactExperiment.method == method,
            )
        ).scalar()
        if existing:
            return {"status": "already_picked"}

        api_key = self._get_llm_key(method)
        if not api_key:
            self.logger.info(f"No API key for {method} — skipping")
            return {"status": "no_api_key"}

        prompt = LLM_EXPERIMENT_PROMPT.format(date=entry_date.isoformat())

        try:
            response_text, model_version = self._call_llm(method, api_key, prompt)
            tickers = self._parse_llm_picks(response_text)
        except Exception as e:
            self.logger.warning(f"LLM call failed for {method}: {e}")
            return {"status": "failed", "error": str(e)}

        if len(tickers) < 3:
            self.logger.warning(f"{method} returned {len(tickers)} picks, need 3")
            return {"status": "insufficient_picks"}

        entry_prices = {t: self._get_latest_price(t) for t in tickers[:3]}

        self.db.add(FactExperiment(
            week_number=week,
            year=year,
            method=method,
            entry_date=entry_date,
            stock_1_ticker=tickers[0],
            stock_1_entry=Decimal(str(entry_prices.get(tickers[0], 0))),
            stock_1_reasoning=response_text[:500],
            stock_2_ticker=tickers[1],
            stock_2_entry=Decimal(str(entry_prices.get(tickers[1], 0))),
            stock_3_ticker=tickers[2],
            stock_3_entry=Decimal(str(entry_prices.get(tickers[2], 0))),
            llm_prompt=prompt[:1000],
            llm_response=response_text[:2000],
            llm_model_version=model_version,
        ))
        self.db.flush()

        return {"status": "picked", "stocks": tickers[:3], "model": model_version}

    # =========================================================================
    # Exit (Friday close)
    # =========================================================================

    def _close_positions(self, exit_date: date, year: int, week: int) -> dict:
        """Close all positions for the week, compute returns, determine winner."""
        experiments = self.db.execute(
            select(FactExperiment).where(
                FactExperiment.year == year,
                FactExperiment.week_number == week,
                FactExperiment.exit_date.is_(None),
            )
        ).scalars().all()

        if not experiments:
            return {"status": "no_open_positions"}

        returns = {}
        for exp in experiments:
            exp_record = cast(Any, exp)
            s1_exit = self._get_latest_price(exp_record.stock_1_ticker)
            s2_exit = self._get_latest_price(exp_record.stock_2_ticker)
            s3_exit = self._get_latest_price(exp_record.stock_3_ticker)

            s1_ret = _calc_return(exp_record.stock_1_entry, s1_exit)
            s2_ret = _calc_return(exp_record.stock_2_entry, s2_exit)
            s3_ret = _calc_return(exp_record.stock_3_entry, s3_exit)
            weekly = round((s1_ret + s2_ret + s3_ret) / 3, 5)

            exp_record.exit_date = exit_date
            exp_record.stock_1_exit = Decimal(str(s1_exit))
            exp_record.stock_2_exit = Decimal(str(s2_exit))
            exp_record.stock_3_exit = Decimal(str(s3_exit))
            exp_record.stock_1_return = Decimal(str(s1_ret))
            exp_record.stock_2_return = Decimal(str(s2_ret))
            exp_record.stock_3_return = Decimal(str(s3_ret))
            exp_record.weekly_return = Decimal(str(weekly))

            returns[exp_record.method] = weekly

        # Determine winner
        if returns:
            winner = max(returns, key=lambda method: returns[method])
            for exp in experiments:
                exp_record = cast(Any, exp)
                exp_record.is_winner = exp_record.method == winner

        self.db.flush()
        return {"status": "closed", "returns": returns, "winner": winner if returns else None}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_latest_price(self, ticker: str) -> float:
        """Get the most recent closing price for a ticker."""
        result = self.db.execute(
            select(FactPrice.close).join(
                DimStock, FactPrice.stock_id == DimStock.stock_id
            ).where(
                DimStock.ticker == ticker
            ).order_by(FactPrice.date.desc()).limit(1)
        ).scalar()
        return float(result) if result else 0.0

    def _get_llm_key(self, method: str) -> str | None:
        if method == "CHATGPT":
            return settings.openai_api_key
        elif method == "GEMINI":
            return settings.google_api_key
        elif method == "GROK":
            return settings.xai_api_key
        return None

    def _call_llm(self, method: str, api_key: str, prompt: str) -> tuple[str, str]:
        """Call LLM API and return (response_text, model_version)."""
        import requests  # type: ignore[import-untyped]

        if method == "CHATGPT":
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 500},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"], data["model"]

        elif method == "GEMINI":
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text, "gemini-2.0-flash"

        elif method == "GROK":
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "grok-3", "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 500},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"], "grok-3"

        raise ValueError(f"Unknown method: {method}")

    def _parse_llm_picks(self, response: str) -> list[str]:
        """Extract ticker symbols from LLM response text."""
        import re
        # Match $TICKER or standalone uppercase 1-5 char words that look like tickers
        pattern = r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{1,5})(?:\s|,|\.|$)'
        matches = re.findall(pattern, response)
        tickers = []
        known_words = {"THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL",
                       "CAN", "HER", "WAS", "ONE", "OUR", "OUT", "HAS", "HIS",
                       "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "SEE", "WAY",
                       "WHO", "DID", "GET", "LET", "SAY", "SHE", "TOO", "USE"}
        for m in matches:
            ticker = m[0] or m[1]
            if ticker and ticker not in known_words and ticker not in tickers:
                tickers.append(ticker)
        return tickers[:3]


def _calc_return(entry: Decimal | None, exit_price: float) -> float:
    if not entry or float(entry) == 0:
        return 0.0
    return round((exit_price - float(entry)) / float(entry), 5)
