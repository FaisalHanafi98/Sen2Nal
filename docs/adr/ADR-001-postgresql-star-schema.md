# ADR-001: PostgreSQL Star Schema over Document Store

**Status**: Accepted
**Date**: 2026-01-12

## Context

Sen2Nal processes structured financial data (OHLCV prices, sentiment scores, calendar features) and needs to support analytical queries across time, stocks, and sectors. The database must handle daily batch inserts (~500 rows/day at scale) and serve dashboard queries with sub-200ms latency.

## Decision

Use PostgreSQL 15 with a star schema design:
- 3 dimension tables: `dim_stocks`, `dim_calendar`, `dim_fear_greed`
- 4 fact tables: `fact_sentiment`, `fact_prices`, `fact_predictions`, `fact_experiment`
- 2 staging tables: `stg_news_raw`, `stg_reddit_raw`

Managed via SQLAlchemy 2.0 ORM with Alembic migrations. Deployed as Docker container (postgres:15-alpine).

## Alternatives Considered

**MongoDB (Document Store)**
- Pros: Flexible schema, easy JSON storage for SHAP values
- Cons: No native JOIN support for star schema queries, weaker ACID guarantees, harder to enforce referential integrity between stocks/dates/scores
- Rejected: Financial data requires strict consistency

**TimescaleDB (Time-Series Extension)**
- Pros: Native time-series compression, hypertables
- Cons: Additional operational complexity, overkill for <10M rows in year 1
- Rejected: Standard PostgreSQL handles our scale. Can migrate later if needed.

**SQLite (Embedded)**
- Pros: Zero-ops, file-based
- Cons: No concurrent access, no production-grade replication
- Rejected: Need concurrent API + dashboard access

## Consequences

- Star schema enables efficient analytical queries (GROUP BY sector, time range)
- Foreign keys enforce data integrity between stocks, dates, and scores
- Composite indexes on (stock_id, date_id) optimize the primary query pattern
- PostgreSQL JSONB column used for SHAP values and topics (structured flexibility within relational model)
- Alembic manages schema evolution without data loss
- Docker deployment keeps infrastructure portable
