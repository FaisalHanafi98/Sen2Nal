# ADR-005: Walk-Forward Validation over K-Fold

**Status**: Accepted
**Date**: 2026-01-12

## Context

Sen2Nal trains XGBoost models on time-series financial data to predict next-day stock direction. The validation methodology must prevent lookahead bias — using future information to predict the past — which is the single most common error in financial ML research (Research KB Source #7).

## Decision

Use walk-forward validation exclusively. Never use standard k-fold cross-validation for time-series financial data.

Walk-forward protocol:
- Training window: 252 trading days (1 year)
- Test window: 21 trading days (1 month)
- Step: Slide forward by 21 days, retrain, test on next 21 days
- No data from the test period is ever visible during training

## Alternatives Considered

**Standard K-Fold Cross-Validation**
- Pros: Maximizes use of limited data, well-understood
- Cons:
  - Introduces lookahead bias: fold 3 might train on March data and test on January data
  - Inflates accuracy by 10-20% compared to walk-forward (Research KB Source #42)
  - Published financial ML papers using k-fold routinely fail to reproduce in live trading
- Rejected: Fundamentally invalid for time-series data

**TimeSeriesSplit (sklearn)**
- Pros: Expanding window respects temporal order
- Cons: Training set grows unboundedly, making early/late folds incomparable
- Rejected: Walk-forward with fixed window is more realistic for production retraining

**Purged K-Fold**
- Pros: Adds gap between train/test to reduce leakage
- Cons: Still allows temporal inversion in some folds, gap size is arbitrary
- Rejected: Walk-forward eliminates the problem entirely rather than mitigating it

## Consequences

- All reported metrics reflect realistic forward-looking performance
- Model accuracy will be lower than k-fold results (typically 5-15% lower) — this is correct, not a bug
- Monthly retraining cadence matches the walk-forward test window (21 trading days)
- Backtesting results are directly comparable to live performance
- Every prediction is made using only information available before the prediction date
- Trade-off accepted: Walk-forward uses less of the available data for training (fixed window vs expanding), but this reflects production reality where old data becomes less relevant
