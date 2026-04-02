"""Initial schema with star schema tables

Revision ID: 001
Revises:
Create Date: 2026-01-12 13:15:00.000000

Aligned with models.py — Integer PKs, full column set.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import BIGINT, JSONB

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # DIMENSION TABLES
    # =========================================================================

    op.create_table(
        'dim_stocks',
        sa.Column('stock_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('ticker', sa.String(10), nullable=False, unique=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('sector', sa.String(100), nullable=False),
        sa.Column('industry', sa.String(100)),
        sa.Column('market_cap', BIGINT),
        sa.Column('sp500_rank', sa.Integer),
        sa.Column('cik', sa.String(20)),
        sa.Column('isin', sa.String(20)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_dim_stocks_ticker', 'dim_stocks', ['ticker'])
    op.create_index('idx_dim_stocks_sector', 'dim_stocks', ['sector'])
    op.create_index('idx_dim_stocks_sp500_rank', 'dim_stocks', ['sp500_rank'])

    op.create_table(
        'dim_calendar',
        sa.Column('date_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('date', sa.Date, nullable=False, unique=True),
        sa.Column('day_of_week', sa.Integer, nullable=False),
        sa.Column('day_of_week_name', sa.String(10), nullable=False),
        sa.Column('day_of_month', sa.Integer, nullable=False),
        sa.Column('week_of_year', sa.Integer, nullable=False),
        sa.Column('month', sa.Integer, nullable=False),
        sa.Column('month_name', sa.String(10), nullable=False),
        sa.Column('quarter', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('is_weekend', sa.Boolean, nullable=False),
        sa.Column('is_trading_day', sa.Boolean, nullable=False),
        sa.Column('is_month_start', sa.Boolean, nullable=False),
        sa.Column('is_month_end', sa.Boolean, nullable=False),
        sa.Column('is_quarter_start', sa.Boolean, nullable=False),
        sa.Column('is_quarter_end', sa.Boolean, nullable=False),
        sa.Column('is_year_start', sa.Boolean, nullable=False),
        sa.Column('is_year_end', sa.Boolean, nullable=False),
        sa.Column('is_us_holiday', sa.Boolean, server_default='false'),
        sa.Column('holiday_name', sa.String(50)),
        sa.Column('trading_days_in_month', sa.Integer),
        sa.Column('trading_day_of_month', sa.Integer),
    )
    op.create_index('idx_dim_calendar_date', 'dim_calendar', ['date'])
    op.create_index('idx_dim_calendar_trading', 'dim_calendar', ['is_trading_day'])
    op.create_index('idx_dim_calendar_year_month', 'dim_calendar', ['year', 'month'])

    op.create_table(
        'dim_fear_greed',
        sa.Column('fg_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dim_calendar.date_id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False, unique=True),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('classification', sa.String(20), nullable=False),
        sa.Column('prev_score', sa.Integer),
        sa.Column('score_change', sa.Integer),
        sa.Column('market_momentum', sa.Integer),
        sa.Column('stock_price_strength', sa.Integer),
        sa.Column('stock_price_breadth', sa.Integer),
        sa.Column('put_call_ratio', sa.Numeric(5, 3)),
        sa.Column('market_volatility', sa.Numeric(5, 2)),
        sa.Column('safe_haven_demand', sa.Integer),
        sa.Column('junk_bond_demand', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint('score >= 0 AND score <= 100', name='ck_fear_greed_score'),
    )
    op.create_index('idx_dim_fear_greed_date', 'dim_fear_greed', ['date'])

    # =========================================================================
    # FACT TABLES
    # =========================================================================

    op.create_table(
        'fact_sentiment',
        sa.Column('sentiment_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('stock_id', sa.Integer, sa.ForeignKey('dim_stocks.stock_id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dim_calendar.date_id'), nullable=False),
        # NLP
        sa.Column('nlp_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('nlp_score_prev', sa.Numeric(5, 4)),
        sa.Column('nlp_momentum', sa.Numeric(5, 4)),
        sa.Column('nlp_trend_days', sa.Integer, server_default='0'),
        sa.Column('nlp_confidence', sa.Numeric(4, 3)),
        # Source breakdown
        sa.Column('news_score', sa.Numeric(5, 4)),
        sa.Column('news_count', sa.Integer, server_default='0'),
        sa.Column('reddit_score', sa.Numeric(5, 4)),
        sa.Column('reddit_count', sa.Integer, server_default='0'),
        # Calendar
        sa.Column('calendar_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('month_avg_return', sa.Numeric(6, 3)),
        sa.Column('month_win_rate', sa.Numeric(4, 3)),
        sa.Column('days_to_earnings', sa.Integer),
        # Combined signal
        sa.Column('combined_score', sa.Numeric(4, 3), nullable=False),
        sa.Column('signal', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Numeric(4, 3), nullable=False),
        # Conflict
        sa.Column('conflict_flag', sa.Boolean, server_default='false'),
        sa.Column('conflict_reason', sa.Text),
        # Topics
        sa.Column('topics', JSONB),
        # Metadata
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('pipeline_run_id', sa.String(50)),
        sa.UniqueConstraint('stock_id', 'date_id', name='uq_sentiment_stock_date'),
    )
    op.create_index('idx_fact_sentiment_stock_date', 'fact_sentiment', ['stock_id', 'date_id'])
    op.create_index('idx_fact_sentiment_date', 'fact_sentiment', ['date_id'])
    op.create_index('idx_fact_sentiment_combined', 'fact_sentiment', ['combined_score'])
    op.create_index('idx_fact_sentiment_signal', 'fact_sentiment', ['signal'])

    op.create_table(
        'fact_prices',
        sa.Column('price_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('stock_id', sa.Integer, sa.ForeignKey('dim_stocks.stock_id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dim_calendar.date_id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('open', sa.Numeric(12, 4), nullable=False),
        sa.Column('high', sa.Numeric(12, 4), nullable=False),
        sa.Column('low', sa.Numeric(12, 4), nullable=False),
        sa.Column('close', sa.Numeric(12, 4), nullable=False),
        sa.Column('adj_close', sa.Numeric(12, 4), nullable=False),
        sa.Column('volume', BIGINT, nullable=False),
        sa.Column('daily_return', sa.Numeric(8, 5)),
        sa.Column('intraday_range', sa.Numeric(8, 5)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('stock_id', 'date_id', name='uq_price_stock_date'),
    )
    op.create_index('idx_fact_prices_stock_date', 'fact_prices', ['stock_id', 'date_id'])
    op.create_index('idx_fact_prices_date', 'fact_prices', ['date_id'])

    op.create_table(
        'fact_predictions',
        sa.Column('prediction_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('stock_id', sa.Integer, sa.ForeignKey('dim_stocks.stock_id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dim_calendar.date_id'), nullable=False),
        sa.Column('prediction_date', sa.Date, nullable=False),
        sa.Column('target_date', sa.Date, nullable=False),
        sa.Column('predicted_direction', sa.String(10), nullable=False),
        sa.Column('predicted_score', sa.Numeric(4, 3), nullable=False),
        sa.Column('predicted_confidence', sa.Numeric(4, 3), nullable=False),
        sa.Column('actual_direction', sa.String(10)),
        sa.Column('actual_return', sa.Numeric(8, 5)),
        sa.Column('prediction_correct', sa.Boolean),
        sa.Column('model_version', sa.String(20), nullable=False),
        sa.Column('feature_importance', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('evaluated_at', sa.DateTime),
        sa.UniqueConstraint('stock_id', 'prediction_date', 'target_date', name='uq_pred_stock_dates'),
    )
    op.create_index('idx_fact_predictions_stock_date', 'fact_predictions', ['stock_id', 'prediction_date'])

    op.create_table(
        'fact_experiment',
        sa.Column('experiment_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('week_number', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('entry_date', sa.Date, nullable=False),
        sa.Column('stock_1_ticker', sa.String(10), nullable=False),
        sa.Column('stock_1_score', sa.Numeric(4, 3)),
        sa.Column('stock_1_entry', sa.Numeric(12, 4)),
        sa.Column('stock_1_reasoning', sa.Text),
        sa.Column('stock_2_ticker', sa.String(10), nullable=False),
        sa.Column('stock_2_score', sa.Numeric(4, 3)),
        sa.Column('stock_2_entry', sa.Numeric(12, 4)),
        sa.Column('stock_2_reasoning', sa.Text),
        sa.Column('stock_3_ticker', sa.String(10), nullable=False),
        sa.Column('stock_3_score', sa.Numeric(4, 3)),
        sa.Column('stock_3_entry', sa.Numeric(12, 4)),
        sa.Column('stock_3_reasoning', sa.Text),
        sa.Column('exit_date', sa.Date),
        sa.Column('stock_1_exit', sa.Numeric(12, 4)),
        sa.Column('stock_2_exit', sa.Numeric(12, 4)),
        sa.Column('stock_3_exit', sa.Numeric(12, 4)),
        sa.Column('stock_1_return', sa.Numeric(8, 5)),
        sa.Column('stock_2_return', sa.Numeric(8, 5)),
        sa.Column('stock_3_return', sa.Numeric(8, 5)),
        sa.Column('weekly_return', sa.Numeric(8, 5)),
        sa.Column('is_winner', sa.Boolean, server_default='false'),
        sa.Column('llm_prompt', sa.Text),
        sa.Column('llm_response', sa.Text),
        sa.Column('llm_model_version', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('year', 'week_number', 'method', name='uq_exp_year_week_method'),
    )
    op.create_index('idx_fact_experiment_week', 'fact_experiment', ['year', 'week_number'])
    op.create_index('idx_fact_experiment_method', 'fact_experiment', ['method'])

    # =========================================================================
    # STAGING TABLES
    # =========================================================================

    op.create_table(
        'stg_news_raw',
        sa.Column('raw_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('external_id', sa.String(100)),
        sa.Column('headline', sa.Text, nullable=False),
        sa.Column('summary', sa.Text),
        sa.Column('url', sa.Text),
        sa.Column('published_at', sa.DateTime),
        sa.Column('fetched_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('is_processed', sa.Boolean, server_default='false'),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('tickers_mentioned', sa.JSON),
        sa.Column('sentiment_score', sa.Numeric(5, 4)),
        sa.Column('sentiment_label', sa.String(20)),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('is_duplicate', sa.Boolean, server_default='false'),
        sa.UniqueConstraint('source', 'external_id', name='uq_news_source_external'),
    )
    op.create_index('idx_stg_news_content_hash', 'stg_news_raw', ['content_hash'])

    op.create_table(
        'stg_reddit_raw',
        sa.Column('raw_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('subreddit', sa.String(50), nullable=False),
        sa.Column('post_id', sa.String(20), nullable=False),
        sa.Column('post_type', sa.String(20), nullable=False),
        sa.Column('title', sa.Text),
        sa.Column('body', sa.Text),
        sa.Column('author', sa.String(50)),
        sa.Column('score', sa.Integer),
        sa.Column('num_comments', sa.Integer),
        sa.Column('created_utc', sa.DateTime),
        sa.Column('fetched_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('is_processed', sa.Boolean, server_default='false'),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('tickers_mentioned', sa.JSON),
        sa.Column('sentiment_score', sa.Numeric(5, 4)),
        sa.Column('sentiment_label', sa.String(20)),
        sa.UniqueConstraint('subreddit', 'post_id', name='uq_reddit_subreddit_post'),
    )


def downgrade() -> None:
    op.drop_table('stg_reddit_raw')
    op.drop_table('stg_news_raw')
    op.drop_table('fact_experiment')
    op.drop_table('fact_predictions')
    op.drop_table('fact_prices')
    op.drop_table('fact_sentiment')
    op.drop_table('dim_fear_greed')
    op.drop_table('dim_calendar')
    op.drop_table('dim_stocks')
