# Sen2Nal — Project Source of Truth

> **System**: Sen2Nal (Multi-Agent Quantitative Sentiment & Financial Intelligence System)
> **Architecture**: FastAPI + PyTorch + HuggingFace Transformers + XGBoost + PostgreSQL + Celery/Redis
> **Governing Document**: `docs/plans/EXECUTION_PLAN_v1.md`
> **Known Issues Register**: `docs/KNOWN_ISSUES.md`
> **Living State**: `CURRENT_MODULE_STATE.md`

---

## 1. Executive Summary
Sen2Nal is a quantitative financial intelligence platform designed to ingest multi-source unstructured financial sentiment (news, social signals, SEC filings), extract named entities, compute sentiment vectors via Transformer models, and generate predictive alpha signals and trade recommendations via multi-agent orchestration.

## 2. Multi-Agent Pipeline Hierarchy
1. **News/Data Ingestion Agent**: Collects financial headlines and market feeds.
2. **Sentiment Extraction Agent (RoBERTa / FinBERT)**: Generates granular sentiment scores.
3. **Pattern & Technical Indicator Agent**: Integrates price action and moving averages.
4. **Experiment & Validation Agent (`ExperimentAgent`)**: Performs walk-forward validation and backtesting.
5. **Portfolio & Signal Agent**: Generates structured signal outputs and alerts.

## 3. Engineering Guidelines & Constraints
- Python 3.11 pinning via Poetry (`poetry.lock`).
- Strict unit testing with deterministic mock fixtures for all external LLM and market feeds.
- Git commit message standard operating procedure strictly enforced (`docs/COMMIT_MESSAGE_SOP.md`).
