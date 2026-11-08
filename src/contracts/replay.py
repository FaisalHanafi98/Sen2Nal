"""Frozen research output bound to one publication input manifest."""

from datetime import date, datetime, timezone
import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, field_validator, model_validator

from src.contracts.publication import (
    CompanyTicker,
    EvidenceVersion,
    FrozenContract,
    PublicationManifest,
)


ArtifactHash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class ScorerArtifact(FrozenContract):
    """Identity of the supplied sentiment scorer and its local assets."""

    scorer: Literal["finbert", "vader"]
    model_id: str = Field(min_length=1, max_length=200)
    revision: str = Field(min_length=1, max_length=200)
    runtime_version: str = Field(min_length=1, max_length=200)
    artifact_hash: ArtifactHash
    tokenizer_hash: ArtifactHash | None = None

    @model_validator(mode="after")
    def tokenizer_matches_scorer(self) -> Self:
        if self.scorer == "finbert" and self.tokenizer_hash is None:
            raise ValueError("FinBERT requires a tokenizer hash")
        if self.scorer == "vader" and self.tokenizer_hash is not None:
            raise ValueError("VADER does not use a tokenizer artifact")
        return self


class SupportingHistory(FrozenContract):
    """Reference to completed history supplied for a research tag."""

    first_date: date
    last_date: date
    available_at: AwareDatetime
    content_hash: ArtifactHash

    @field_validator("available_at")
    @classmethod
    def canonical_time(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def ordered_history(self) -> Self:
        if self.first_date > self.last_date:
            raise ValueError("Supporting history dates are out of order")
        return self


class ScoreComponent(FrozenContract):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,49}$")
    value: float
    meaning: str = Field(min_length=1, max_length=300)


class SignalSnapshot(FrozenContract):
    """One supplied tag and the references needed to explain it."""

    member: CompanyTicker
    research_tag: str = Field(min_length=1, max_length=100)
    scores: tuple[ScoreComponent, ...] = Field(min_length=1, max_length=20)
    scorer: ScorerArtifact
    history: SupportingHistory
    evidence: tuple[EvidenceVersion, ...] = Field(min_length=1)

    @field_validator("scores")
    @classmethod
    def unique_scores(cls, scores: tuple[ScoreComponent, ...]) -> tuple[ScoreComponent, ...]:
        if len({score.name for score in scores}) != len(scores):
            raise ValueError("Score component names must be unique")
        return tuple(sorted(scores, key=lambda score: score.name))

    @field_validator("evidence")
    @classmethod
    def unique_evidence(cls, evidence: tuple[EvidenceVersion, ...]) -> tuple[EvidenceVersion, ...]:
        if len(set(evidence)) != len(evidence):
            raise ValueError("Signal evidence references must be unique")
        return tuple(sorted(evidence, key=lambda record: record.model_dump_json()))


class ResearchReplay(FrozenContract):
    """Replay candidate with frozen outputs and the original input manifest."""

    schema_version: Literal["sen2nal-replay-v1"] = "sen2nal-replay-v1"
    manifest: PublicationManifest
    signals: tuple[SignalSnapshot, ...] = Field(max_length=50)

    @model_validator(mode="after")
    def inputs_match_manifest(self) -> Self:
        if not self.signals:
            return self
        manifest = self.manifest
        if (manifest.availability_state != "eligible_inputs" or manifest.universe is None
                or manifest.cutoff is None):
            raise ValueError("Signals require a manifest with eligible inputs")

        members = set(manifest.universe.members)
        evidence = set(manifest.evidence)
        used: set[CompanyTicker] = set()
        for signal in self.signals:
            if signal.member not in members or signal.member in used:
                raise ValueError("Each signal must match distinct manifest membership")
            if not evidence.issuperset(signal.evidence):
                raise ValueError("Signal evidence must match the selected manifest versions")
            if (signal.history.last_date >= manifest.trading_date
                    or signal.history.available_at > manifest.cutoff):
                raise ValueError("Supporting history must be complete and available by the cutoff")
            used.add(signal.member)
        object.__setattr__(self, "signals", tuple(sorted(self.signals, key=lambda row: row.member.rank)))
        return self

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    @property
    def replay_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
