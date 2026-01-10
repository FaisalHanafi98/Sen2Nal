"""
Configuration management for Sen2Nal application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------------
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    enable_cors: bool = Field(default=True, description="Enable CORS")

    # -----------------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql://sen2nal_user:sen2nal_password@localhost:5432/sen2nal",
        description="PostgreSQL connection URL",
    )
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="sen2nal")
    db_user: str = Field(default="sen2nal_user")
    db_password: str = Field(default="sen2nal_password")

    # -----------------------------------------------------------------------------
    # AWS
    # -----------------------------------------------------------------------------
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    s3_bucket_name: Optional[str] = Field(default=None)

    # -----------------------------------------------------------------------------
    # API Keys - Data Sources
    # -----------------------------------------------------------------------------
    alpha_vantage_api_key: Optional[str] = Field(default=None)
    newsapi_api_key: Optional[str] = Field(default=None)
    reddit_client_id: Optional[str] = Field(default=None)
    reddit_client_secret: Optional[str] = Field(default=None)
    reddit_user_agent: str = Field(default="Sen2Nal/1.0")

    # -----------------------------------------------------------------------------
    # LLM API Keys
    # -----------------------------------------------------------------------------
    openai_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    xai_api_key: Optional[str] = Field(default=None)

    # -----------------------------------------------------------------------------
    # API Server
    # -----------------------------------------------------------------------------
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)

    # -----------------------------------------------------------------------------
    # Streamlit
    # -----------------------------------------------------------------------------
    streamlit_port: int = Field(default=8501)
    streamlit_server_address: str = Field(default="0.0.0.0")

    # -----------------------------------------------------------------------------
    # Scheduler
    # -----------------------------------------------------------------------------
    pipeline_schedule_cron: str = Field(default="0 6 * * *", description="6 AM daily")
    enable_scheduler: bool = Field(default=False)

    # -----------------------------------------------------------------------------
    # Model Configuration
    # -----------------------------------------------------------------------------
    finbert_model_name: str = Field(default="ProsusAI/finbert")
    finbert_batch_size: int = Field(default=16)
    finbert_max_length: int = Field(default=512)

    # Signal Combination
    nlp_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    calendar_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    conflict_threshold: float = Field(default=0.30)

    # Calendar Pattern
    calendar_lookback_months: int = Field(default=18)

    # -----------------------------------------------------------------------------
    # Rate Limiting
    # -----------------------------------------------------------------------------
    alpha_vantage_rate_limit: int = Field(default=5, description="requests per minute")
    newsapi_rate_limit: int = Field(default=100, description="requests per day")
    reddit_rate_limit: int = Field(default=60, description="requests per minute")

    # -----------------------------------------------------------------------------
    # Security
    # -----------------------------------------------------------------------------
    secret_key: str = Field(default="change-me-in-production")
    allowed_hosts: str = Field(default="localhost,127.0.0.1")

    # -----------------------------------------------------------------------------
    # Feature Flags
    # -----------------------------------------------------------------------------
    enable_experiment_tracking: bool = Field(default=True)
    enable_backtest: bool = Field(default=False)
    enable_model_retraining: bool = Field(default=False)

    @field_validator("nlp_weight", "calendar_weight")
    @classmethod
    def validate_weights_sum_to_one(cls, v, info):
        """Ensure NLP + Calendar weights sum to 1.0"""
        if info.field_name == "calendar_weight":
            nlp_weight = info.data.get("nlp_weight", 0.6)
            if abs(nlp_weight + v - 1.0) > 0.01:
                raise ValueError(
                    f"nlp_weight ({nlp_weight}) + calendar_weight ({v}) must sum to 1.0"
                )
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()


# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------


def setup_logging() -> logging.Logger:
    """Configure logging for the application."""

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # File handler
    from datetime import datetime

    log_file = logs_dir / f"sen2nal_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set third-party loggers to WARNING
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger


# Initialize logging
logger = setup_logging()
