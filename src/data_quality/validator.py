"""Pipeline stage validator using Pydantic data contracts.

Validates data between pipeline stages. Each stage maps to a Pydantic
contract model. Records pass/fail per record and raises
DataContractViolation if any records fail validation.

Usage:
    from src.data_quality import validate_stage

    result = validate_stage("ingestion", records)
    if not result.is_valid:
        # handle errors
"""

from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import BaseModel, ValidationError

from src.contracts.base import DataContractViolation
from src.contracts.calendar import CalendarOutput
from src.contracts.features import FeatureOutput
from src.contracts.ingestion import IngestionOutput
from src.contracts.prediction import PredictionOutput
from src.contracts.sentiment import SentimentOutput

STAGE_CONTRACTS: dict[str, type[BaseModel]] = {
    "ingestion": IngestionOutput,
    "sentiment": SentimentOutput,
    "calendar": CalendarOutput,
    "features": FeatureOutput,
    "prediction": PredictionOutput,
}


@dataclass
class StageError:
    """A single record validation failure."""

    index: int
    errors: list[dict[str, Any]]


@dataclass
class ValidationResult:
    """Result of validating a batch of records against a stage contract."""

    stage: str
    total: int
    errors: list[StageError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def passed(self) -> int:
        return self.total - len(self.errors)

    def summary(self) -> str:
        return f"Stage '{self.stage}': {self.passed}/{self.total} passed, {len(self.errors)} failed"


def validate_stage(
    stage: str,
    records: list[dict[str, Any]],
    raise_on_failure: bool = False,
) -> ValidationResult:
    """Validate a list of records against the contract for a pipeline stage.

    Args:
        stage: Pipeline stage name (ingestion, sentiment, calendar, features, prediction).
        records: List of dicts to validate.
        raise_on_failure: If True, raise DataContractViolation on any failure.

    Returns:
        ValidationResult with pass/fail details.

    Raises:
        ValueError: If stage name is unknown.
        DataContractViolation: If raise_on_failure=True and validation fails.
    """
    if stage not in STAGE_CONTRACTS:
        raise ValueError(f"Unknown stage '{stage}'. Valid: {list(STAGE_CONTRACTS.keys())}")

    contract = STAGE_CONTRACTS[stage]
    errors: list[StageError] = []

    for i, record in enumerate(records):
        try:
            contract.model_validate(record)
        except ValidationError as e:
            errors.append(StageError(index=i, errors=cast(list[dict[str, Any]], e.errors())))

    result = ValidationResult(stage=stage, total=len(records), errors=errors)

    if raise_on_failure and not result.is_valid:
        error_details = [{"index": e.index, "errors": e.errors} for e in errors]
        raise DataContractViolation(stage=stage, errors=error_details)

    return result
