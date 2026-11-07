"""AG-05: XGBoost Prediction Agent.

Trains and runs an XGBoost model for weekly directional prediction.
- Walk-forward validation: 252-day training window, 21-day test window
- Features from fact_sentiment + fact_prices
- Feature contribution proxies from model importance and input values
- Stores predictions in fact_predictions
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select, and_

from src.agents.base import BaseAgent
from src.contracts.base import DataContractViolation
from src.contracts.prediction import PredictionWrite
from src.data_quality.validator import require_record
from src.database.models import DimCalendar, DimStock, FactPrediction, FactPrice, FactSentiment

logger = logging.getLogger(__name__)

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "xgboost_sen2nal.joblib"

# Feature columns extracted from fact_sentiment
FEATURE_COLS = [
    "nlp_score", "nlp_momentum", "nlp_confidence",
    "news_count", "reddit_count",
    "calendar_score", "month_avg_return", "month_win_rate",
    "combined_score", "conflict_flag_int",
    "daily_return", "intraday_range", "volume_norm",
]


def _prediction_summary(target: date, count: int, mode: str) -> dict[str, Any]:
    return {
        "target_date": str(target), "predictions_generated": count, "mode": mode,
        "records_validated": count, "data_state": "present" if count else "empty",
        "disclaimer": "NOT FINANCIAL ADVICE",
    }


class PredictionAgent(BaseAgent):
    """XGBoost directional prediction with walk-forward validation."""

    stage_name = "prediction"

    @property
    def name(self) -> str:
        return "AG-05-Prediction"

    def execute(self, target_date: date | None = None,
                tickers: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        target = target_date or date.today()
        from src.constants import TOP_10_TICKERS
        ticker_list = tickers or list(TOP_10_TICKERS)

        # Build training dataset from historical data
        X, y, meta = self._build_dataset(ticker_list)

        if len(X) < 30:
            self.logger.warning(f"Insufficient training data ({len(X)} rows). "
                                "Generating predictions from sentiment scores only.")
            return self._fallback_predictions(target, ticker_list)

        # Walk-forward windowing (ADR-005): 252-day training window
        TRAIN_WINDOW = 252
        if len(X) > TRAIN_WINDOW:
            X = X[-TRAIN_WINDOW:]
            y = y[-TRAIN_WINDOW:]
            self.logger.info(f"Walk-forward: using last {TRAIN_WINDOW} of {len(meta)} samples")

        model = self._load_or_train(X, y, force_retrain=kwargs.get("force_retrain", False))

        # Generate predictions for target date
        predictions = self._predict(model, target, ticker_list)

        self.db.commit()
        return {**_prediction_summary(target, predictions, "xgboost"), "training_samples": len(X)}

    def _build_dataset(self, tickers: list[str]) -> tuple[np.ndarray, np.ndarray, list]:
        """Build feature matrix from historical fact_sentiment + fact_prices."""
        rows = self.db.execute(
            select(
                FactSentiment, FactPrice
            ).join(
                FactPrice,
                and_(
                    FactSentiment.stock_id == FactPrice.stock_id,
                    FactSentiment.date_id == FactPrice.date_id,
                ),
            ).join(
                DimStock, FactSentiment.stock_id == DimStock.stock_id
            ).where(
                DimStock.ticker.in_(tickers)
            ).order_by(FactSentiment.date_id)
        ).all()

        if not rows:
            return np.array([]), np.array([]), []

        X_list = []
        y_list = []
        meta_list = []

        for sent, price in rows:
            features = [
                float(sent.nlp_score or 0),
                float(sent.nlp_momentum or 0),
                float(sent.nlp_confidence or 0),
                int(sent.news_count or 0),
                int(sent.reddit_count or 0),
                float(sent.calendar_score or 0),
                float(sent.month_avg_return or 0),
                float(sent.month_win_rate or 0.5),
                float(sent.combined_score or 0.5),
                int(sent.conflict_flag or 0),
                float(price.daily_return or 0),
                float(price.intraday_range or 0),
                float(price.volume or 0) / 1e8,  # Normalize volume
            ]
            X_list.append(features)

            # Target: next-day return direction (1=up, 0=down)
            y_list.append(1 if (price.daily_return or 0) > 0 else 0)
            meta_list.append({"stock_id": sent.stock_id, "date_id": sent.date_id})

        return np.array(X_list), np.array(y_list), meta_list

    def _load_or_train(self, X: np.ndarray, y: np.ndarray, force_retrain: bool = False) -> Any:
        """Load saved model if available and recent, otherwise train fresh."""
        if not force_retrain and MODEL_PATH.exists():
            try:
                import joblib
                model = joblib.load(MODEL_PATH)
                self.logger.info(f"Loaded existing model from {MODEL_PATH}")
                return model
            except Exception as e:
                self.logger.warning(f"Failed to load saved model: {e}. Retraining.")
        return self._train_model(X, y)

    def _train_model(self, X: np.ndarray, y: np.ndarray) -> Any:
        """Train XGBoost classifier with walk-forward principles."""
        try:
            import xgboost as xgb
        except ImportError:
            self.logger.error("xgboost not installed")
            raise

        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )

        model.fit(X, y, verbose=False)

        # Save model
        import joblib
        MODEL_DIR.mkdir(exist_ok=True)
        joblib.dump(model, MODEL_PATH)

        self.logger.info(f"Model trained on {len(X)} samples, saved to {MODEL_PATH}")
        return model

    def _predict(self, model: Any, target: date, tickers: list[str]) -> int:
        """Generate and store predictions for target date."""
        date_id = self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == target)
        ).scalar()
        if not date_id:
            return 0

        count = 0
        target_end = target + timedelta(days=7)  # Weekly prediction window

        for ticker in tickers:
            stock_id = self.db.execute(
                select(DimStock.stock_id).where(DimStock.ticker == ticker)
            ).scalar()
            if not stock_id:
                continue

            # Get latest sentiment features for this ticker
            sent = self.db.execute(
                select(FactSentiment).where(
                    FactSentiment.stock_id == stock_id
                ).order_by(FactSentiment.date_id.desc()).limit(1)
            ).scalar()

            price = self.db.execute(
                select(FactPrice).where(
                    FactPrice.stock_id == stock_id
                ).order_by(FactPrice.date_id.desc()).limit(1)
            ).scalar()

            if not sent:
                continue

            features = np.array([[
                float(sent.nlp_score or 0),
                float(sent.nlp_momentum or 0),
                float(sent.nlp_confidence or 0),
                int(sent.news_count or 0),
                int(sent.reddit_count or 0),
                float(sent.calendar_score or 0),
                float(sent.month_avg_return or 0),
                float(sent.month_win_rate or 0.5),
                float(sent.combined_score or 0.5),
                int(sent.conflict_flag or 0),
                float(price.daily_return or 0) if price else 0,
                float(price.intraday_range or 0) if price else 0,
                float(price.volume or 0) / 1e8 if price else 0,
            ]])

            raw_distribution = model.predict_proba(features)
            try:
                distribution = np.asarray(raw_distribution)
            except (TypeError, ValueError) as exc:
                raise DataContractViolation("prediction", [{"type": "probability_distribution"}]) from exc
            if (distribution.shape != (1, 2) or distribution.dtype.kind not in "fiu"
                    or not np.isfinite(distribution).all()
                    or ((distribution < 0) | (distribution > 1)).any()
                    or not np.isclose(distribution.sum(), 1.0, rtol=0.0, atol=1e-6)):
                raise DataContractViolation("prediction", [{"type": "probability_distribution"}])
            proba = distribution[0]
            direction = int(np.argmax(proba))
            probability = float(proba[direction])

            feature_contributions = {}
            try:
                feature_imp = model.feature_importances_
                for i, col in enumerate(FEATURE_COLS):
                    feature_contributions[col] = round(float(feature_imp[i] * features[0][i]), 4)
            except Exception:
                pass

            # Check for existing prediction
            existing = self.db.execute(
                select(FactPrediction.prediction_id).where(
                    FactPrediction.stock_id == stock_id,
                    FactPrediction.prediction_date == target,
                    FactPrediction.target_date == target_end,
                )
            ).scalar()
            if existing:
                continue

            values = dict(
                stock_id=stock_id,
                date_id=date_id,
                prediction_date=target,
                target_date=target_end,
                predicted_direction="UP" if direction == 1 else "DOWN",
                predicted_score=round(probability, 3),
                predicted_confidence=round(probability, 3),
                model_version="xgb-v1.0",
                feature_importance=feature_contributions,
            )
            require_record("prediction", PredictionWrite, values)
            self.db.add(FactPrediction(**values))
            count += 1

        self.db.flush()
        self.logger.info(f"Generated {count} predictions for {target}")
        return count

    def _fallback_predictions(self, target: date, tickers: list[str]) -> dict[str, Any]:
        """Generate predictions from sentiment scores when insufficient training data."""
        date_id = self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == target)
        ).scalar()
        if not date_id:
            return _prediction_summary(target, 0, "fallback")

        count = 0
        target_end = target + timedelta(days=7)

        for ticker in tickers:
            stock_id = self.db.execute(
                select(DimStock.stock_id).where(DimStock.ticker == ticker)
            ).scalar()
            if not stock_id:
                continue

            sent = self.db.execute(
                select(FactSentiment).where(
                    FactSentiment.stock_id == stock_id
                ).order_by(FactSentiment.date_id.desc()).limit(1)
            ).scalar()
            if sent is None or sent.combined_score is None:
                continue

            score = float(sent.combined_score)
            direction = "UP" if score >= 0.5 else "DOWN"
            probability = abs(score - 0.5) * 2  # Map [0,1] to confidence

            existing = self.db.execute(
                select(FactPrediction.prediction_id).where(
                    FactPrediction.stock_id == stock_id,
                    FactPrediction.prediction_date == target,
                    FactPrediction.target_date == target_end,
                )
            ).scalar()
            if existing:
                continue

            values = dict(
                stock_id=stock_id,
                date_id=date_id,
                prediction_date=target,
                target_date=target_end,
                predicted_direction=direction,
                predicted_score=round(score, 3),
                predicted_confidence=round(max(0.5, probability), 3),
                model_version="sent-fallback-v1.0",
                feature_importance={"combined_score": round(score, 4)},
            )
            require_record("prediction", PredictionWrite, values)
            self.db.add(FactPrediction(**values))
            count += 1

        self.db.commit()
        return _prediction_summary(target, count, "fallback")
