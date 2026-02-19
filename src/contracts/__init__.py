"""Data contracts for inter-agent communication in the Sen2Nal pipeline."""

from src.contracts.base import DataContractViolation
from src.contracts.calendar import CalendarOutput
from src.contracts.features import FeatureOutput
from src.contracts.ingestion import IngestionOutput
from src.contracts.prediction import PredictionOutput
from src.contracts.sentiment import SentimentOutput

__all__ = [
    "DataContractViolation",
    "IngestionOutput",
    "SentimentOutput",
    "CalendarOutput",
    "FeatureOutput",
    "PredictionOutput",
]
