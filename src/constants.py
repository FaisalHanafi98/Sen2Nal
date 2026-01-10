"""
Global constants for Sen2Nal application.
"""

from enum import Enum

# -----------------------------------------------------------------------------
# Signal Classifications
# -----------------------------------------------------------------------------


class SignalType(str, Enum):
    """Trading signal classifications."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    AVOID = "AVOID"


# Signal thresholds (combined score 0-1)
SIGNAL_THRESHOLDS = {
    SignalType.STRONG_BUY: 0.70,
    SignalType.BUY: 0.55,
    SignalType.HOLD: 0.45,
    # Below 0.45 = AVOID
}


# -----------------------------------------------------------------------------
# Fear & Greed Classifications
# -----------------------------------------------------------------------------


class FearGreedClassification(str, Enum):
    """Fear & Greed Index classifications."""

    EXTREME_FEAR = "Extreme Fear"
    FEAR = "Fear"
    NEUTRAL = "Neutral"
    GREED = "Greed"
    EXTREME_GREED = "Extreme Greed"


FEAR_GREED_THRESHOLDS = {
    FearGreedClassification.EXTREME_FEAR: (0, 25),
    FearGreedClassification.FEAR: (25, 45),
    FearGreedClassification.NEUTRAL: (45, 55),
    FearGreedClassification.GREED: (55, 75),
    FearGreedClassification.EXTREME_GREED: (75, 100),
}


# -----------------------------------------------------------------------------
# GICS Sectors
# -----------------------------------------------------------------------------

GICS_SECTORS = [
    "Technology",
    "Healthcare",
    "Financials",
    "Consumer Discretionary",
    "Communication Services",
    "Industrials",
    "Consumer Staples",
    "Energy",
    "Utilities",
    "Real Estate",
    "Materials",
]


# -----------------------------------------------------------------------------
# Top 10 Stocks by Market Cap (S&P 500)
# -----------------------------------------------------------------------------

TOP_10_TICKERS = [
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corporation
    "GOOGL",  # Alphabet Inc.
    "AMZN",  # Amazon.com Inc.
    "NVDA",  # NVIDIA Corporation
    "META",  # Meta Platforms Inc.
    "TSLA",  # Tesla Inc.
    "BRK.B",  # Berkshire Hathaway Inc.
    "JPM",  # JPMorgan Chase & Co.
    "V",  # Visa Inc.
]


# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------


class DataSource(str, Enum):
    """Data source identifiers."""

    ALPHA_VANTAGE = "alpha_vantage"
    NEWSAPI = "newsapi"
    YAHOO = "yahoo"
    REDDIT = "reddit"
    FEAR_GREED = "fear_greed"


# -----------------------------------------------------------------------------
# Experiment Methods
# -----------------------------------------------------------------------------


class ExperimentMethod(str, Enum):
    """Methods participating in the weekly experiment."""

    SEN2NAL = "SEN2NAL"
    CHATGPT = "CHATGPT"
    GEMINI = "GEMINI"
    GROK = "GROK"


# -----------------------------------------------------------------------------
# Direction Classifications
# -----------------------------------------------------------------------------


class Direction(str, Enum):
    """Price direction classifications."""

    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


# -----------------------------------------------------------------------------
# Pipeline Status
# -----------------------------------------------------------------------------


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# -----------------------------------------------------------------------------
# Time Constants
# -----------------------------------------------------------------------------

# Trading days per year (approximate)
TRADING_DAYS_PER_YEAR = 252

# Market hours (EST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Pipeline schedule (EST)
PIPELINE_RUN_HOUR = 6
PIPELINE_RUN_MINUTE = 0


# -----------------------------------------------------------------------------
# Model Constants
# -----------------------------------------------------------------------------

# FinBERT sentiment mapping
FINBERT_LABEL_MAP = {
    0: 1.0,  # positive
    1: -1.0,  # negative
    2: 0.0,  # neutral
}

FINBERT_LABELS = ["positive", "negative", "neutral"]


# -----------------------------------------------------------------------------
# API Constants
# -----------------------------------------------------------------------------

# API Version
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Rate limiting
DEFAULT_RATE_LIMIT = 60  # requests per minute
DEFAULT_RATE_LIMIT_PERIOD = 60  # seconds


# -----------------------------------------------------------------------------
# Database Constants
# -----------------------------------------------------------------------------

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

# Lookback periods
DEFAULT_HISTORY_DAYS = 30
MAX_HISTORY_DAYS = 540  # 18 months


# -----------------------------------------------------------------------------
# Experiment Constants
# -----------------------------------------------------------------------------

EXPERIMENT_TOTAL_WEEKS = 8
EXPERIMENT_STOCKS_PER_METHOD = 3

# LLM Prompt Template
LLM_EXPERIMENT_PROMPT = """You are a financial analyst. Based on current market conditions as of {date},
select exactly 3 S&P 500 stocks that you believe will perform best over the
next 5 trading days (Monday open to Friday close).

Consider:
- Recent news sentiment
- Technical factors
- Seasonal patterns
- Market conditions

Respond with exactly 3 ticker symbols and a brief reasoning for each.
Format: TICKER: Reasoning"""


# -----------------------------------------------------------------------------
# Legal Disclaimers (for UI)
# -----------------------------------------------------------------------------

FOOTER_DISCLAIMER = """⚠️ Disclaimer: Sen2Nal is for informational purposes only
and is NOT financial advice. Investing involves risk of loss.
Past performance does not guarantee future results.
The creator(s) are not liable for any financial losses."""

SIGNAL_WARNING = """⚠️ IMPORTANT: This signal is for INFORMATIONAL PURPOSES ONLY.

• NOT financial advice or a recommendation to buy/sell
• Based on experimental sentiment analysis
• Past performance does NOT guarantee future results
• Always consult a licensed financial advisor
• Never invest money you cannot afford to lose"""

EXPERIMENT_DISCLAIMER = """📊 RESEARCH EXPERIMENT DISCLAIMER

This experiment comparing Sen2Nal vs LLM stock picks is conducted for
EDUCATIONAL AND RESEARCH PURPOSES ONLY.

• Results are HYPOTHETICAL and based on paper trading
• No actual money is invested in this experiment
• Performance shown does NOT reflect actual trading results
• Transaction costs, slippage, and taxes are not included
• DO NOT use these results to make investment decisions"""
