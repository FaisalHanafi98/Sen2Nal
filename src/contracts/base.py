"""Base contract definitions and exceptions."""

from pydantic import BaseModel, ConfigDict


class StrictContract(BaseModel):
    """Base class for all pipeline data contracts. Rejects extra fields."""

    model_config = ConfigDict(strict=True, extra="forbid")


class DataContractViolation(Exception):
    """Raised when data fails contract validation at an agent boundary."""

    def __init__(self, stage: str, errors: list[dict]) -> None:
        self.stage = stage
        self.errors = errors
        summary = f"{len(errors)} validation error(s) at stage '{stage}'"
        super().__init__(summary)
