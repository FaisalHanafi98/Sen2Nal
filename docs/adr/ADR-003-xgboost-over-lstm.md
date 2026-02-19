# ADR-003: XGBoost over LSTM for Prediction

**Status**: Accepted
**Date**: 2026-01-12

## Context

Sen2Nal needs a model to predict next-day stock price direction (up/down) using combined sentiment, calendar, and market features. The model must be interpretable (SHAP explainability is a core requirement), trainable on limited data (~252 trading days per stock), and fast to retrain monthly.

## Decision

Use XGBoost for directional stock prediction with SHAP values for every prediction.

- Target: Binary classification (next-day direction)
- Validation: Walk-forward (see ADR-005)
- Explainability: SHAP values decompose every prediction into feature contributions
- Benchmark: 90%+ directional accuracy in academic studies with proper features (Research KB Source #18)

## Alternatives Considered

**LSTM (Long Short-Term Memory)**
- Pros: Captures sequential patterns in time series, handles variable-length sequences
- Cons:
  - Requires 1000+ samples for stable training; we have ~252/year per stock
  - Training time: 10-30 minutes vs XGBoost's 2-5 seconds
  - SHAP integration is indirect and computationally expensive for RNNs
  - Hyperparameter tuning is significantly more complex
  - Prone to overfitting on small financial datasets
- Rejected: Insufficient data volume and no native SHAP support

**Random Forest**
- Pros: Interpretable, handles mixed feature types
- Cons: Generally lower accuracy than XGBoost on tabular data, slower inference at scale
- Rejected: XGBoost consistently outperforms in benchmarks

**Linear Models (Logistic Regression)**
- Pros: Fully interpretable, fast, minimal overfitting risk
- Cons: Cannot capture non-linear feature interactions (sentiment * calendar effects)
- Rejected: Non-linear interactions are core to our hypothesis

## Consequences

- XGBoost trains in 2-5 seconds — enables monthly retraining without GPU
- SHAP TreeExplainer provides exact feature contributions in milliseconds
- Every prediction includes a transparent breakdown: "FinBERT sentiment (+0.3), holiday decay (-0.1), fear index (+0.2)"
- Small model size (~100KB) — trivial to version and deploy
- Walk-forward validation prevents temporal data leakage (see ADR-005)
- Trade-off accepted: XGBoost does not capture sequential patterns the way LSTMs can. If sequence modeling proves necessary, we can ensemble XGBoost + lightweight temporal model later.
