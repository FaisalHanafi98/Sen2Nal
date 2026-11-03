"""Pure publication input contracts; no evaluation or provider execution."""

from datetime import date, datetime, time, timezone
from typing import Literal, Self, Sequence, cast
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, ConfigDict, Field, field_validator, model_validator

from src.contracts.base import StrictContract


class FrozenContract(StrictContract):
    """Immutable typed values, including immutable nested collections."""

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)


class EvidenceVersion(FrozenContract):
    """A source version reference; unknown availability is retained as unknown."""

    source: str = Field(min_length=1, max_length=200)
    source_id: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=200)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    published_at: AwareDatetime | None = None
    available_at: AwareDatetime | None = None
    ingested_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None = None

    @field_validator("published_at", "available_at", "ingested_at", "expires_at")
    @classmethod
    def canonical_time(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(timezone.utc) if value is not None else None

    @model_validator(mode="after")
    def timestamp_order(self) -> Self:
        known = [value for value in (self.published_at, self.available_at, self.ingested_at)
                 if value is not None]
        if known != sorted(known):
            raise ValueError("Invalid evidence timestamp order")
        return self


class ExcludedEvidence(FrozenContract):
    evidence: EvidenceVersion
    reason: Literal["unknown_availability", "after_cutoff", "stale", "superseded"]


class EvidenceSelection(FrozenContract):
    selected: tuple[EvidenceVersion, ...]
    excluded: tuple[ExcludedEvidence, ...]


def publication_cutoff(trading_date: date) -> datetime:
    """Return the owner's 08:00 New York boundary for a supplied session date."""
    return datetime.combine(trading_date, time(8), tzinfo=ZoneInfo("America/New_York"))


def select_evidence(
    evidence: Sequence[EvidenceVersion], cutoff: datetime
) -> EvidenceSelection:
    """Select original versions available to this pipeline by the cutoff."""
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("The cutoff must be timezone-aware")
    eligible: dict[tuple[str, str], list[EvidenceVersion]] = {}
    selected: list[EvidenceVersion] = []
    excluded: list[ExcludedEvidence] = []
    for record in sorted(set(evidence), key=lambda item: item.model_dump_json()):
        times = (record.published_at, record.available_at, record.ingested_at)
        if any(value is None for value in times):
            excluded.append(ExcludedEvidence(evidence=record, reason="unknown_availability"))
        elif any(value is not None and value > cutoff for value in times):
            excluded.append(ExcludedEvidence(evidence=record, reason="after_cutoff"))
        else:
            eligible.setdefault((record.source, record.source_id), []).append(record)
    for identity in sorted(eligible):
        versions: dict[str, EvidenceVersion] = {}
        for record in eligible[identity]:
            prior = versions.get(record.version)
            if prior is not None:
                content = (record.content_hash, record.published_at, record.available_at,
                           record.expires_at)
                prior_content = (prior.content_hash, prior.published_at, prior.available_at,
                                 prior.expires_at)
                if content != prior_content:
                    raise ValueError("Conflicting evidence version")
                if cast(datetime, record.ingested_at) >= cast(datetime, prior.ingested_at):
                    continue
            versions[record.version] = record
        records = list(versions.values())
        newest_at = max(cast(datetime, record.available_at) for record in records)
        newest_records = [record for record in records if record.available_at == newest_at]
        if len(newest_records) != 1:
            raise ValueError("Ambiguous evidence revision")
        newest = newest_records[0]
        if newest.expires_at is not None and newest.expires_at <= cutoff:
            excluded.append(ExcludedEvidence(evidence=newest, reason="stale"))
        else:
            selected.append(newest)
        excluded.extend(
            ExcludedEvidence(evidence=record, reason="superseded")
            for record in records if record != newest
        )
    excluded.sort(key=lambda item: item.model_dump_json())
    return EvidenceSelection(selected=tuple(selected), excluded=tuple(excluded))
