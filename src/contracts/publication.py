"""Pure publication input contracts; no evaluation or provider execution."""

from datetime import date, datetime, time, timezone
import hashlib
import json
from typing import Any, Literal, Self, Sequence, cast
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, ConfigDict, Field, field_validator, model_validator

from src.contracts.base import StrictContract


class FrozenContract(StrictContract):
    """Immutable typed values, including immutable nested collections."""

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    @field_validator("*")
    @classmethod
    def nonblank_text(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            raise ValueError("Contract text must not be blank")
        return value


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


class USSession(FrozenContract):
    """One supplied exchange-calendar record, including explicit closed sessions."""

    exchange: Literal["XNYS", "XNAS"]
    trading_date: date
    source: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=200)
    available_at: AwareDatetime
    is_trading_day: bool
    opens_at: AwareDatetime | None = None
    closes_at: AwareDatetime | None = None

    @field_validator("available_at", "opens_at", "closes_at")
    @classmethod
    def canonical_time(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(timezone.utc) if value is not None else None

    @model_validator(mode="after")
    def valid_session(self) -> Self:
        if not self.is_trading_day:
            if self.opens_at is not None or self.closes_at is not None:
                raise ValueError("A closed session cannot have opening/closing times")
        elif self.opens_at is None or self.closes_at is None:
            raise ValueError("An open session requires opening and closing times")
        elif self.opens_at >= self.closes_at or any(
            value.astimezone(ZoneInfo("America/New_York")).date() != self.trading_date
            for value in (self.opens_at, self.closes_at)
        ):
            raise ValueError("Invalid exchange session interval")
        return self


class CompanyTicker(FrozenContract):
    company_id: str = Field(min_length=1, max_length=200)
    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,9}$")
    country: Literal["US"]
    rank: int = Field(ge=1, le=50)


class UniverseSnapshot(FrozenContract):
    """Supplied dated top-50 membership; source truth still needs verification."""

    selection_rule: Literal["largest_50_us_companies_by_market_cap"]
    source: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=200)
    policy_reference: str = Field(min_length=1, max_length=200)
    share_class_policy: str = Field(min_length=1, max_length=1000)
    rebalance_policy: str = Field(min_length=1, max_length=1000)
    ranked_at: AwareDatetime
    available_at: AwareDatetime
    effective_from: date
    effective_until: date
    members: tuple[CompanyTicker, ...] = Field(min_length=50, max_length=50)

    @field_validator("ranked_at", "available_at")
    @classmethod
    def canonical_time(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)

    @field_validator("members")
    @classmethod
    def unique_members(cls, value: tuple[CompanyTicker, ...]) -> tuple[CompanyTicker, ...]:
        if any(len({getattr(member, field) for member in value}) != 50
               for field in ("company_id", "ticker", "rank")):
            raise ValueError("Company, ticker and rank must each be unique")
        return tuple(sorted(value, key=lambda member: member.rank))

    @model_validator(mode="after")
    def valid_interval(self) -> Self:
        if self.effective_from >= self.effective_until or self.ranked_at > self.available_at:
            raise ValueError("Invalid universe effective interval or timestamp order")
        return self


class PublicationManifest(FrozenContract):
    """Original input references with structural/as-of availability checks.

    Supplied provenance is not verified provider truth, policy approval, source
    rights or model quality. This contract does not represent a published tag.
    """

    schema_version: Literal["sen2nal-evidence-v1"] = "sen2nal-evidence-v1"
    trading_date: date
    cutoff: AwareDatetime | None = None
    publication_timezone: Literal["America/New_York"] = "America/New_York"
    run_id: str = Field(min_length=1, max_length=200)
    method_version: str = Field(min_length=1, max_length=200)
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[EvidenceVersion, ...]
    calendar: USSession | None = None
    universe: UniverseSnapshot | None = None
    disclaimer: Literal["NOT FINANCIAL ADVICE"] = "NOT FINANCIAL ADVICE"

    @model_validator(mode="after")
    def eligible_evidence(self) -> Self:
        expected_cutoff = publication_cutoff(self.trading_date)
        if self.cutoff is not None and self.cutoff != expected_cutoff:
            raise ValueError("Manifest cutoff must be 08:00 America/New_York")
        object.__setattr__(self, "cutoff", expected_cutoff.astimezone(timezone.utc))
        selection = select_evidence(self.evidence, expected_cutoff)
        if selection.excluded:
            raise ValueError("Manifest evidence must contain only selected eligible versions")
        object.__setattr__(self, "evidence", selection.selected)
        return self

    @property
    def availability_state(self) -> Literal["withheld", "no_data", "eligible_inputs"]:
        if self.unavailable_reasons:
            return "withheld"
        return "eligible_inputs" if self.evidence else "no_data"

    @property
    def unavailable_reasons(self) -> tuple[str, ...]:
        reasons = []
        cutoff = publication_cutoff(self.trading_date)
        if self.calendar is None:
            reasons.append("calendar_unavailable")
        else:
            if self.calendar.trading_date != self.trading_date:
                reasons.append("calendar_date_mismatch")
            if self.calendar.available_at > cutoff:
                reasons.append("calendar_after_cutoff")
            if not self.calendar.is_trading_day:
                reasons.append("non_trading_day")
            elif self.calendar.opens_at is not None and self.calendar.opens_at <= cutoff:
                reasons.append("cutoff_not_before_session")
        if self.universe is None:
            reasons.append("universe_unavailable")
        else:
            if not self.universe.effective_from <= self.trading_date < self.universe.effective_until:
                reasons.append("universe_not_effective")
            if self.universe.available_at > cutoff or self.universe.ranked_at > cutoff:
                reasons.append("universe_after_cutoff")
        return tuple(reasons)

    def canonical_json(self) -> str:
        """Serialise only frozen input facts, independent of dictionary ordering."""
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    @property
    def manifest_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


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
