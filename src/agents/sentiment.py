"""AG-02: Sentiment Scoring Agent.

Processes raw news and Reddit posts using FinBERT for financial sentiment analysis.
- Reads unprocessed records from stg_news_raw and stg_reddit_raw
- Runs FinBERT inference in batches
- Applies time-decay weighting (recent articles weighted higher)
- Aggregates per-ticker daily sentiment scores
- Stores results back to staging tables and computes NLP component for fact_sentiment
"""

import logging
import math
from datetime import datetime
from typing import Any

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.agents.base import BaseAgent
from src.config import settings
from src.database.models import StgNewsRaw, StgRedditRaw

logger = logging.getLogger(__name__)

# Time decay parameter (λ): higher = faster decay of older articles
TIME_DECAY_LAMBDA = 0.1


class SentimentAgent(BaseAgent):
    """Scores raw text with FinBERT and aggregates per-ticker sentiment."""

    stage_name = "sentiment"

    @property
    def name(self) -> str:
        return "AG-02-Sentiment"

    def __init__(self, db: Session, run_id: str | None = None):
        super().__init__(db, run_id)
        self._model = None
        self._tokenizer = None

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        # Load model lazily (first run downloads ~400MB)
        self._load_model()

        # Process news
        news_count = self._process_news()

        # Process Reddit
        reddit_count = self._process_reddit()

        self.db.commit()
        return {
            "news_processed": news_count,
            "reddit_processed": reddit_count,
        }

    # =========================================================================
    # Model loading
    # =========================================================================

    def _load_model(self) -> None:
        """Load FinBERT model and tokenizer. Falls back to VADER if unavailable."""
        if self._model is not None:
            return

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            model_name = settings.finbert_model_name
            self.logger.info(f"Loading FinBERT model: {model_name}")
            import torch
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self._model.to(self._device)
            self._model.eval()
            self._model_type = "finbert"
            self.logger.info(f"FinBERT loaded on {self._device}")
        except Exception as e:
            self.logger.warning(f"FinBERT load failed ({e}), falling back to VADER")
            self._model_type = "vader"
            try:
                from nltk.sentiment.vader import SentimentIntensityAnalyzer
                import nltk
                nltk.download("vader_lexicon", quiet=True)
                self._model = SentimentIntensityAnalyzer()
            except Exception as ve:
                raise RuntimeError(f"Neither FinBERT nor VADER available: {ve}")

    # =========================================================================
    # Scoring functions
    # =========================================================================

    def _score_text(self, text: str) -> tuple[float, float]:
        """Score a single text. Returns (sentiment_score, confidence).

        sentiment_score: -1.0 (bearish) to +1.0 (bullish)
        confidence: 0.0 to 1.0
        """
        if not text or len(text.strip()) < 5:
            return 0.0, 0.0

        if self._model_type == "finbert":
            return self._score_finbert(text)
        else:
            return self._score_vader(text)

    def _score_finbert(self, text: str) -> tuple[float, float]:
        """Score text using FinBERT. Returns (score, confidence)."""
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=settings.finbert_max_length,
            padding=True,
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]

        # FinBERT labels: positive=0, negative=1, neutral=2
        pos, neg, neu = probs[0].item(), probs[1].item(), probs[2].item()

        # Map to [-1, 1]: positive → +1, negative → -1
        score = pos - neg
        confidence = max(pos, neg, neu)

        return round(score, 4), round(confidence, 4)

    def _score_vader(self, text: str) -> tuple[float, float]:
        """Score text using VADER. Returns (score, confidence)."""
        scores = self._model.polarity_scores(text)
        compound = scores["compound"]  # Already -1 to +1
        # Confidence from the absolute compound + non-neutral proportion
        confidence = abs(compound) * 0.5 + (1.0 - scores["neu"]) * 0.5
        return round(compound, 4), round(min(confidence, 1.0), 4)

    def _score_batch(self, texts: list[str]) -> list[tuple[float, float]]:
        """Score a batch of texts. More efficient for FinBERT."""
        if self._model_type == "vader" or not texts:
            return [self._score_text(t) for t in texts]

        import torch

        results = []
        batch_size = settings.finbert_batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self._tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=settings.finbert_max_length,
                padding=True,
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)

            for j in range(len(batch)):
                pos = probs[j][0].item()
                neg = probs[j][1].item()
                neu = probs[j][2].item()
                score = pos - neg
                confidence = max(pos, neg, neu)
                results.append((round(score, 4), round(confidence, 4)))

        return results

    # =========================================================================
    # Process staging tables
    # =========================================================================

    def _process_news(self) -> int:
        """Score unprocessed news articles and update staging records."""
        unprocessed = self.db.execute(
            select(StgNewsRaw).where(StgNewsRaw.is_processed == False).limit(500)
        ).scalars().all()

        if not unprocessed:
            self.logger.info("No unprocessed news articles")
            return 0

        texts = [f"{r.headline}. {r.summary or ''}" for r in unprocessed]
        scores = self._score_batch(texts)

        now = datetime.utcnow()
        for record, (score, confidence) in zip(unprocessed, scores):
            record.sentiment_score = score
            record.sentiment_label = _classify_sentiment(score)
            record.is_processed = True
            record.processed_at = now

        self.db.flush()
        self.logger.info(f"Scored {len(unprocessed)} news articles")
        return len(unprocessed)

    def _process_reddit(self) -> int:
        """Score unprocessed Reddit posts and update staging records."""
        unprocessed = self.db.execute(
            select(StgRedditRaw).where(StgRedditRaw.is_processed == False).limit(500)
        ).scalars().all()

        if not unprocessed:
            self.logger.info("No unprocessed Reddit posts")
            return 0

        texts = [f"{r.title or ''}. {r.body or ''}" for r in unprocessed]
        scores = self._score_batch(texts)

        now = datetime.utcnow()
        for record, (score, confidence) in zip(unprocessed, scores):
            record.sentiment_score = score
            record.sentiment_label = _classify_sentiment(score)
            record.is_processed = True
            record.processed_at = now

        self.db.flush()
        self.logger.info(f"Scored {len(unprocessed)} Reddit posts")
        return len(unprocessed)


# =============================================================================
# Aggregation helpers (used by FeatureAgent to build fact_sentiment NLP scores)
# =============================================================================

def aggregate_ticker_sentiment(
    news_records: list[StgNewsRaw],
    reddit_records: list[StgRedditRaw],
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Aggregate scored staging records into per-ticker NLP sentiment.

    Applies time-decay weighting: score * e^(-λ * hours_old).
    Returns dict with nlp_score, nlp_confidence, news_score, news_count,
    reddit_score, reddit_count.
    """
    ref = reference_time or datetime.utcnow()

    def _weighted_avg(records: list, text_time_attr: str) -> tuple[float, int]:
        if not records:
            return 0.0, 0
        weights = []
        scores = []
        for r in records:
            if r.sentiment_score is None:
                continue
            pub_time = getattr(r, text_time_attr, None)
            if pub_time:
                hours_old = (ref - pub_time).total_seconds() / 3600.0
                weight = math.exp(-TIME_DECAY_LAMBDA * max(hours_old, 0))
            else:
                weight = 0.5  # Default weight for records without timestamp
            weights.append(weight)
            scores.append(float(r.sentiment_score))

        if not scores:
            return 0.0, 0

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0, len(scores)

        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        return round(weighted_score, 4), len(scores)

    news_score, news_count = _weighted_avg(news_records, "published_at")
    reddit_score, reddit_count = _weighted_avg(reddit_records, "created_utc")

    # Combine: news weighted higher for reliability
    total = news_count + reddit_count
    if total == 0:
        nlp_score = 0.0
        nlp_confidence = 0.0
    else:
        news_weight = 0.6
        reddit_weight = 0.4
        if news_count == 0:
            nlp_score = reddit_score
        elif reddit_count == 0:
            nlp_score = news_score
        else:
            nlp_score = news_score * news_weight + reddit_score * reddit_weight
        nlp_confidence = min(1.0, total / 20.0)  # Max confidence at 20+ sources

    return {
        "nlp_score": round(nlp_score, 4),
        "nlp_confidence": round(nlp_confidence, 4),
        "news_score": news_score,
        "news_count": news_count,
        "reddit_score": reddit_score,
        "reddit_count": reddit_count,
    }


def _classify_sentiment(score: float) -> str:
    if score > 0.15:
        return "positive"
    elif score < -0.15:
        return "negative"
    return "neutral"
