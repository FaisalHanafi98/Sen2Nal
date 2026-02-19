# ADR-004: Batch Processing over Real-Time Streaming

**Status**: Accepted
**Date**: 2026-01-12

## Context

Sen2Nal analyzes daily stock sentiment for S&P 500 stocks. The question is whether to process data in real-time (as news arrives) or in daily batches (after market close). This affects infrastructure complexity, cost, and operational overhead.

## Decision

Use daily batch processing. The pipeline runs once per day after market close (6 PM ET):

1. Fetch news/social data for the day
2. Run FinBERT sentiment scoring
3. Compute calendar features
4. Build feature vectors
5. Generate predictions
6. Store results in PostgreSQL
7. Dashboard reads from DB

Orchestrated via APScheduler (already in dependencies). No streaming infrastructure.

## Alternatives Considered

**Apache Kafka + Streaming**
- Pros: Real-time sentiment updates, event-driven architecture
- Cons:
  - Infrastructure: Kafka broker + Zookeeper + consumer groups = 3+ additional services
  - Cost: $50-200/month for managed Kafka vs $0 for cron-triggered batch
  - Complexity: Message serialization, offset management, exactly-once semantics
  - Overkill: Daily stock analysis does not benefit from sub-second latency
- Rejected: 10x infrastructure cost for zero business value in this use case

**Apache Airflow**
- Pros: DAG-based orchestration, retries, monitoring
- Cons: Heavyweight (requires webserver + scheduler + DB), overkill for a single daily pipeline
- Rejected: APScheduler handles our single-pipeline case adequately

**AWS Lambda + EventBridge**
- Pros: Serverless, pay-per-invocation
- Cons: Cold start latency with FinBERT (~500MB model), 15-minute execution limit may be tight for full pipeline
- Rejected: Model size and execution time make Lambda impractical without significant engineering

## Consequences

- Simple infrastructure: PostgreSQL + Python process + APScheduler
- Predictable costs: No streaming infrastructure to maintain
- Easy debugging: Each pipeline run is a discrete, reproducible execution
- Dashboard data is updated once daily — users see "as of market close" data
- Trade-off accepted: No intraday sentiment updates. If real-time becomes necessary (e.g., trading signals during market hours), we would add a lightweight WebSocket layer, not full Kafka.
