"""Tests for the data quality validator.

Verifies that validate_stage() correctly accepts valid records,
rejects invalid records, and raises DataContractViolation when configured.
"""

from datetime import date, datetime

import pytest

from src.contracts.base import DataContractViolation
from src.data_quality.validator import ValidationResult, validate_stage


# -- Valid records accepted ----------------------------------------------------

class TestValidRecords:

    def test_ingestion_valid(self):
        record = {
            "source": "newsapi",
            "raw_text": "Apple stock surges on earnings beat",
            "ticker_mentions": ["AAPL"],
            "published_at": datetime(2026, 3, 20, 14, 0),
            "fetched_at": datetime(2026, 3, 20, 15, 0),
            "external_id": "abc123",
            "content_hash": "a" * 64,
        }
        result = validate_stage("ingestion", [record])
        assert result.is_valid
        assert result.passed == 1
        assert result.total == 1

    def test_sentiment_valid(self):
        record = {
            "ticker": "AAPL",
            "sentiment_score": 0.75,
            "confidence": 0.92,
            "source_count": 5,
            "model_used": "finbert",
            "processing_timestamp": datetime(2026, 3, 20, 15, 0),
        }
        result = validate_stage("sentiment", [record])
        assert result.is_valid

    def test_calendar_valid(self):
        record = {
            "ticker": "MSFT",
            "date": date(2026, 3, 20),
            "holiday_decay": -0.05,
            "day_of_week_effect": 0.10,
            "earnings_proximity": None,
            "month_avg_return": 0.011,
            "month_win_rate": 0.65,
            "trading_day_of_month": 15,
            "calendar_score": 0.12,
        }
        result = validate_stage("calendar", [record])
        assert result.is_valid

    def test_multiple_valid_records(self):
        records = [
            {
                "ticker": "AAPL",
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "source_count": 3,
                "model_used": "vader",
                "processing_timestamp": datetime(2026, 3, 20, 15, 0),
            },
            {
                "ticker": "MSFT",
                "sentiment_score": -0.3,
                "confidence": 0.6,
                "source_count": 1,
                "model_used": "finbert",
                "processing_timestamp": datetime(2026, 3, 20, 15, 5),
            },
        ]
        result = validate_stage("sentiment", records)
        assert result.is_valid
        assert result.passed == 2

    def test_empty_records_list_is_valid(self):
        result = validate_stage("ingestion", [])
        assert result.is_valid
        assert result.total == 0


# -- Invalid records rejected --------------------------------------------------

class TestInvalidRecords:

    def test_ingestion_missing_required_field(self):
        record = {
            "source": "newsapi",
            # raw_text missing
            "fetched_at": datetime(2026, 3, 20, 15, 0),
            "content_hash": "a" * 64,
        }
        result = validate_stage("ingestion", [record])
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].index == 0

    def test_sentiment_score_out_of_range(self):
        record = {
            "ticker": "AAPL",
            "sentiment_score": 1.5,  # exceeds max 1.0
            "confidence": 0.8,
            "source_count": 3,
            "model_used": "finbert",
            "processing_timestamp": datetime(2026, 3, 20, 15, 0),
        }
        result = validate_stage("sentiment", [record])
        assert not result.is_valid

    def test_ingestion_invalid_source(self):
        record = {
            "source": "twitter",  # not in Literal
            "raw_text": "some text",
            "fetched_at": datetime(2026, 3, 20, 15, 0),
            "content_hash": "a" * 64,
        }
        result = validate_stage("ingestion", [record])
        assert not result.is_valid

    def test_content_hash_wrong_length(self):
        record = {
            "source": "newsapi",
            "raw_text": "some text",
            "fetched_at": datetime(2026, 3, 20, 15, 0),
            "content_hash": "short",  # must be exactly 64 chars
        }
        result = validate_stage("ingestion", [record])
        assert not result.is_valid

    def test_invalid_model_used(self):
        record = {
            "ticker": "AAPL",
            "sentiment_score": 0.5,
            "confidence": 0.8,
            "source_count": 3,
            "model_used": "gpt4",  # not in Literal["finbert", "vader"]
            "processing_timestamp": datetime(2026, 3, 20, 15, 0),
        }
        result = validate_stage("sentiment", [record])
        assert not result.is_valid

    def test_calendar_score_out_of_bounds(self):
        record = {
            "ticker": "AAPL",
            "date": date(2026, 3, 20),
            "holiday_decay": -0.05,
            "day_of_week_effect": 0.10,
            "earnings_proximity": None,
            "month_avg_return": 0.011,
            "month_win_rate": 0.65,
            "trading_day_of_month": 15,
            "calendar_score": 1.5,  # exceeds max 1.0
        }
        result = validate_stage("calendar", [record])
        assert not result.is_valid

    def test_extra_fields_rejected(self):
        """StrictContract has extra='forbid' — unknown fields should fail."""
        record = {
            "ticker": "AAPL",
            "sentiment_score": 0.5,
            "confidence": 0.8,
            "source_count": 3,
            "model_used": "finbert",
            "processing_timestamp": datetime(2026, 3, 20, 15, 0),
            "bonus_field": "not_allowed",
        }
        result = validate_stage("sentiment", [record])
        assert not result.is_valid

    def test_mixed_valid_and_invalid(self):
        """One valid + one invalid = partial failure."""
        records = [
            {
                "ticker": "AAPL",
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "source_count": 3,
                "model_used": "finbert",
                "processing_timestamp": datetime(2026, 3, 20, 15, 0),
            },
            {
                "ticker": "MSFT",
                "sentiment_score": 999,  # out of range
                "confidence": 0.8,
                "source_count": 3,
                "model_used": "finbert",
                "processing_timestamp": datetime(2026, 3, 20, 15, 0),
            },
        ]
        result = validate_stage("sentiment", records)
        assert not result.is_valid
        assert result.passed == 1
        assert len(result.errors) == 1
        assert result.errors[0].index == 1


# -- Error handling ------------------------------------------------------------

class TestErrorHandling:

    def test_unknown_stage_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown stage"):
            validate_stage("nonexistent", [{}])

    def test_raise_on_failure_raises_contract_violation(self):
        bad_record = {"source": "newsapi"}  # missing required fields
        with pytest.raises(DataContractViolation) as exc_info:
            validate_stage("ingestion", [bad_record], raise_on_failure=True)
        assert exc_info.value.stage == "ingestion"
        assert len(exc_info.value.errors) > 0

    def test_raise_on_failure_false_does_not_raise(self):
        bad_record = {"source": "newsapi"}
        result = validate_stage("ingestion", [bad_record], raise_on_failure=False)
        assert not result.is_valid


# -- ValidationResult API ------------------------------------------------------

class TestValidationResult:

    def test_summary_format(self):
        result = ValidationResult(stage="test", total=5)
        assert "5/5 passed" in result.summary()
        assert "0 failed" in result.summary()

    def test_is_valid_with_no_errors(self):
        result = ValidationResult(stage="test", total=3)
        assert result.is_valid
        assert result.passed == 3

    def test_is_valid_false_with_errors(self):
        from src.data_quality.validator import StageError
        result = ValidationResult(
            stage="test",
            total=2,
            errors=[StageError(index=0, errors=[{"msg": "bad"}])],
        )
        assert not result.is_valid
        assert result.passed == 1
