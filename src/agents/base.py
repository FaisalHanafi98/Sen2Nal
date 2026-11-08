"""Base agent class for the Sen2Nal pipeline."""

import logging
import uuid
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from src.contracts.base import DataContractViolation


_RUN_METADATA = frozenset({"status", "agent", "run_id", "elapsed_seconds", "error_code"})


class IncompleteStageData(Exception):
    """A stage could not collect all of its requested inputs."""


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
        started = perf_counter()
        self.logger.info(f"[{self.run_id}] Starting {self.name}")
        result: dict[str, Any]
        try:
            payload = self.execute(**kwargs)
            if not isinstance(payload, dict) or _RUN_METADATA.intersection(payload):
                result = {"status": "invalid", "error_code": "invalid_stage_payload",
                          "error": "Stage returned an invalid execution payload"}
            elif payload.get("error") not in (None, ""):
                result = {"status": "failed", "error_code": "stage_execution_error",
                          "error": "Stage reported an execution error"}
            else:
                self._validate_output(payload)
                result = {**payload, "status": "success"}
        except DataContractViolation:
            result = {"status": "invalid", "error_code": "data_contract_violation",
                      "error": "Stage output contains validation errors"}
        except IncompleteStageData:
            result = {"status": "partial", "error_code": "stage_input_incomplete",
                      "error": "Stage could not collect all requested inputs"}
        except Exception:
            result = {"status": "failed", "error_code": "stage_exception",
                      "error": "Stage execution failed"}

        elapsed = perf_counter() - started
        if result["status"] == "success":
            self.logger.info("[%s] %s completed in %.1fs", self.run_id, self.name, elapsed)
        else:
            self.logger.error("[%s] %s returned %s after %.1fs (%s)", self.run_id,
                              self.name, result["status"], elapsed, result["error_code"])
            self.db.rollback()
        return {**result, "agent": self.name, "run_id": self.run_id, "elapsed_seconds": elapsed}
