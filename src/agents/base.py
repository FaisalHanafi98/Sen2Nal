"""Base agent class for the Sen2Nal pipeline."""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session


class BaseAgent(ABC):
    """Base class for all pipeline agents.

    Each agent represents a stage in the data pipeline:
    Ingestion → Sentiment → Calendar → Features → Prediction → Experiment

    Subclasses can opt into output validation by setting `stage_name`
    and implementing `_validation_records()`.
    """

    stage_name: str | None = None

    def __init__(self, db: Session, run_id: str | None = None):
        self.db = db
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        self.logger = logging.getLogger(f"sen2nal.{self.name}")
        self._start_time: datetime | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier used in logging and tracking."""

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Run the agent's main logic. Returns a result summary dict."""

    def _validation_records(self, result: dict[str, Any]) -> list[dict[str, Any]] | None:
        """Extract validatable records from execute() output.

        Override in subclasses that produce contract-validatable data.
        Return None to skip validation.
        """
        return None

    def _validate_output(self, result: dict[str, Any]) -> None:
        """Run data contract validation on agent output if configured.

        Raises DataContractViolation if any records fail validation,
        which causes the pipeline runner to halt at this stage.
        """
        if self.stage_name is None:
            return

        records = self._validation_records(result)
        if records is None or len(records) == 0:
            return

        from src.data_quality.validator import validate_stage
        validation = validate_stage(self.stage_name, records)
        if not validation.is_valid:
            self.logger.error(
                f"[{self.run_id}] {self.name} output validation FAILED: {validation.summary()}"
            )
            from src.contracts.base import DataContractViolation
            error_details = [
                {"index": e.index, "errors": e.errors} for e in validation.errors
            ]
            raise DataContractViolation(stage=self.stage_name, errors=error_details)
        else:
            self.logger.info(
                f"[{self.run_id}] {self.name} output validated: {validation.total} records OK"
            )

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute with logging, validation, and error handling wrapper."""
        self._start_time = datetime.utcnow()
        self.logger.info(f"[{self.run_id}] Starting {self.name}")
        try:
            result = self.execute(**kwargs)
            self._validate_output(result)
            elapsed = (datetime.utcnow() - self._start_time).total_seconds()
            self.logger.info(f"[{self.run_id}] {self.name} completed in {elapsed:.1f}s")
            return {"status": "success", "agent": self.name, "run_id": self.run_id,
                    "elapsed_seconds": elapsed, **result}
        except Exception as e:
            elapsed = (datetime.utcnow() - self._start_time).total_seconds()
            self.logger.error(f"[{self.run_id}] {self.name} failed after {elapsed:.1f}s: {e}")
            self.db.rollback()
            return {"status": "failed", "agent": self.name, "run_id": self.run_id,
                    "elapsed_seconds": elapsed, "error": str(e)}
