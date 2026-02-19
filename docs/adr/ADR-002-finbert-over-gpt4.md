# ADR-002: FinBERT over GPT-4 for Sentiment Analysis

**Status**: Accepted
**Date**: 2026-01-12

## Context

Sen2Nal needs to score financial news and social media text for sentiment. The model must handle hundreds of articles daily with consistent, reproducible results. Cost and latency matter because this runs as a daily batch pipeline, not a one-off analysis.

## Decision

Use ProsusAI/FinBERT as the primary sentiment model, with VADER as a secondary model for social media text.

- FinBERT: 88% F1 score on financial text (Research KB Source #12)
- VADER: Faster, handles emoji/slang in Reddit posts
- Combined scoring: `(P_pos - P_neg) * confidence`

## Alternatives Considered

**GPT-4 / GPT-4o via API**
- Pros: Higher general reasoning, handles nuanced context
- Cons:
  - Cost: ~$0.06/article vs ~$0.002/article (FinBERT local inference)
  - At 200 articles/day = $12/day (GPT-4) vs $0.40/day (FinBERT)
  - At 1000 articles/day = $60/day vs $2/day
  - Latency: 1-3s per API call vs 0.13s local inference
  - Non-deterministic: Same input produces different outputs across calls
  - Dependency: Requires API key, internet, OpenAI uptime
- Rejected: 30x cost premium with no reproducibility guarantee

**Generic BERT (bert-base-uncased)**
- Pros: Widely available, well-documented
- Cons: Not pre-trained on financial text, 14% lower F1 than FinBERT on financial sentiment tasks
- Rejected: Domain-specific pre-training is critical for financial NLP

**LLaMA / Open-Source LLMs**
- Pros: No API cost, local inference
- Cons: 7B+ parameter models require GPU with 16GB+ VRAM, much slower inference than FinBERT (110M params)
- Rejected: FinBERT is purpose-built and 60x smaller

## Consequences

- FinBERT runs locally — no API dependency, no per-call cost after initial download (~400MB)
- Inference at ~0.13s/article enables batch processing of 200+ articles in under 30 seconds
- Reproducible: Same input always produces same output (deterministic)
- Model cached locally after first download via HuggingFace hub
- VADER handles Reddit/social media where FinBERT's formal training is less applicable
- Trade-off accepted: FinBERT cannot reason about complex financial narratives the way GPT-4 can, but for sentiment classification (positive/negative/neutral), it is sufficient and superior in cost/speed
