"""Synthetic publication inputs; no exchange/provider/database access."""

from datetime import date, datetime, timezone
import hashlib

import pytest
from pydantic import ValidationError

from src.contracts.publication import (
    CompanyTicker, EvidenceVersion, PublicationManifest, USSession, UniverseSnapshot,
    publication_cutoff, select_evidence,
)


@pytest.mark.parametrize(("day", "utc_hour"), [(date(2026, 7, 6), 12), (date(2026, 11, 4), 13)])
def test_cutoff_stays_at_eight_new_york_across_dst(day, utc_hour):
    cutoff = publication_cutoff(day)
    assert cutoff.hour == 8
    assert cutoff.tzinfo.key == "America/New_York"
    assert cutoff.astimezone(timezone.utc) == datetime(
        day.year, day.month, day.day, utc_hour, tzinfo=timezone.utc
    )


def evidence(version="original", **changes):
    values = {
        "source": "synthetic-news",
        "source_id": "story-1",
        "version": version,
        "content_hash": "a" * 64,
        "published_at": datetime(2026, 11, 4, 11, tzinfo=timezone.utc),
        "available_at": datetime(2026, 11, 4, 11, 1, tzinfo=timezone.utc),
        "ingested_at": datetime(2026, 11, 4, 11, 2, tzinfo=timezone.utc),
    }
    return EvidenceVersion(**(values | changes))


def test_revision_seen_after_cutoff_cannot_replace_the_original():
    original = evidence()
    late = evidence(
        "revised",
        content_hash="b" * 64,
        available_at=datetime(2026, 11, 4, 13, 1, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 11, 4, 13, 2, tzinfo=timezone.utc),
    )
    result = select_evidence([late, original], publication_cutoff(date(2026, 11, 4)))
    assert result.selected == (original,)
    assert [(item.evidence.version, item.reason) for item in result.excluded] == [
        ("revised", "after_cutoff")
    ]


def test_latest_eligible_revision_wins_independent_of_order_or_retry():
    original = evidence()
    revised = evidence(
        "revised", content_hash="b" * 64,
        available_at=datetime(2026, 11, 4, 12, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 11, 4, 12, 1, tzinfo=timezone.utc),
    )
    cutoff = publication_cutoff(date(2026, 11, 4))
    first = select_evidence([original, revised, revised], cutoff)
    second = select_evidence([revised, original], cutoff)
    assert first == second
    assert first.selected == (revised,)
    assert [(item.evidence.version, item.reason) for item in first.excluded] == [
        ("original", "superseded")
    ]


@pytest.mark.parametrize("field", ["published_at", "available_at", "ingested_at"])
def test_unknown_timestamp_is_excluded_without_inventing_availability(field):
    record = evidence(**{field: None})
    result = select_evidence([record], publication_cutoff(date(2026, 11, 4)))
    assert result.selected == ()
    assert result.excluded[0].reason == "unknown_availability"


@pytest.mark.parametrize("field", ["published_at", "available_at", "ingested_at"])
def test_naive_source_timestamp_is_rejected(field):
    with pytest.raises(ValidationError, match="timezone"):
        evidence(**{field: datetime(2026, 11, 4, 11)})


def test_explicitly_expired_evidence_has_a_stale_state():
    record = evidence(expires_at=datetime(2026, 11, 4, 12, tzinfo=timezone.utc))
    result = select_evidence([record], publication_cutoff(date(2026, 11, 4)))
    assert result.selected == ()
    assert result.excluded[0].reason == "stale"


def test_conflicting_hashes_for_one_source_version_block_selection():
    with pytest.raises(ValueError, match="Conflicting evidence version"):
        select_evidence(
            [evidence(), evidence(content_hash="b" * 64)],
            publication_cutoff(date(2026, 11, 4)),
        )


def test_simultaneous_distinct_revisions_have_no_arbitrary_winner():
    with pytest.raises(ValueError, match="Ambiguous evidence revision"):
        select_evidence(
            [evidence(), evidence("second", content_hash="b" * 64)],
            publication_cutoff(date(2026, 11, 4)),
        )


def test_receipt_cannot_precede_known_source_availability():
    with pytest.raises(ValidationError, match="timestamp order"):
        evidence(ingested_at=datetime(2026, 11, 4, 10, tzinfo=timezone.utc))


def test_naive_cutoff_is_refused_even_when_there_are_no_records():
    with pytest.raises(ValueError, match="timezone-aware"):
        select_evidence([], datetime(2026, 11, 4, 8))


def test_stale_revision_does_not_resurrect_superseded_content():
    revised = evidence(
        "revised", content_hash="b" * 64,
        available_at=datetime(2026, 11, 4, 12, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 11, 4, 12, 1, tzinfo=timezone.utc),
        expires_at=datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc),
    )
    result = select_evidence([evidence(), revised], publication_cutoff(date(2026, 11, 4)))
    assert result.selected == ()
    assert {item.reason for item in result.excluded} == {"superseded", "stale"}


def test_cutoff_is_inclusive_but_a_late_receipt_is_excluded():
    cutoff = publication_cutoff(date(2026, 11, 4))
    on_time = evidence(published_at=cutoff, available_at=cutoff, ingested_at=cutoff)
    late = evidence(
        "late", published_at=cutoff, available_at=cutoff,
        ingested_at=cutoff.replace(microsecond=1),
    )
    result = select_evidence([late, on_time], cutoff)
    assert result.selected == (on_time,)
    assert result.excluded[0].reason == "after_cutoff"


def test_retry_keeps_first_receipt_and_timestamp_offsets_are_canonical():
    first = evidence()
    retry = evidence(ingested_at=datetime(2026, 11, 4, 12, tzinfo=timezone.utc))
    cutoff = publication_cutoff(date(2026, 11, 4))
    assert select_evidence([retry, first], cutoff).selected == (first,)
    same_instant = evidence(
        published_at=first.published_at.astimezone(cutoff.tzinfo),
        available_at=first.available_at.astimezone(cutoff.tzinfo),
        ingested_at=first.ingested_at.astimezone(cutoff.tzinfo),
    )
    assert same_instant.model_dump_json() == first.model_dump_json()
    with pytest.raises(ValidationError, match="frozen"):
        first.content_hash = "b" * 64


def manifest(**changes):
    values = {
        "trading_date": date(2026, 11, 4),
        "run_id": "synthetic-run",
        "method_version": "synthetic-method-v1",
        "configuration_hash": "c" * 64,
        "evidence": (evidence(),),
    }
    return PublicationManifest(**(values | changes))


def test_manifest_withholds_when_calendar_and_universe_are_unavailable():
    result = manifest()
    assert result.availability_state == "withheld"
    assert result.unavailable_reasons == ("calendar_unavailable", "universe_unavailable")


def session(**changes):
    values = {
        "exchange": "XNYS", "trading_date": date(2026, 11, 4),
        "source": "synthetic-exchange", "version": "fixture-v1",
        "available_at": datetime(2026, 11, 3, 12, tzinfo=timezone.utc),
        "is_trading_day": True,
        "opens_at": datetime(2026, 11, 4, 14, 30, tzinfo=timezone.utc),
        "closes_at": datetime(2026, 11, 4, 21, tzinfo=timezone.utc),
    }
    return USSession(**(values | changes))


def universe(**changes):
    values = {
        "selection_rule": "largest_50_us_companies_by_market_cap",
        "source": "synthetic-ranking", "version": "fixture-v1",
        "policy_reference": "synthetic-policy-only",
        "share_class_policy": "Synthetic fixture; no owner policy selected",
        "rebalance_policy": "Synthetic fixture; no cadence selected",
        "ranked_at": datetime(2026, 11, 2, 12, tzinfo=timezone.utc),
        "available_at": datetime(2026, 11, 3, 12, tzinfo=timezone.utc),
        "effective_from": date(2026, 11, 3), "effective_until": date(2026, 11, 5),
        "members": tuple(
            CompanyTicker(company_id=f"synthetic-{index}", ticker=f"T{index}",
                          country="US", rank=index + 1)
            for index in range(50)
        ),
    }
    return UniverseSnapshot(**(values | changes))


def test_complete_supplied_inputs_are_distinct_from_no_data():
    context = {"calendar": session(), "universe": universe()}
    assert manifest(**context).availability_state == "eligible_inputs"
    empty = manifest(evidence=(), **context)
    assert empty.availability_state == "no_data"
    assert empty.disclaimer == "NOT FINANCIAL ADVICE"


@pytest.mark.parametrize(("changes", "reason"), [
    ({"calendar": session(is_trading_day=False, opens_at=None, closes_at=None)},
     "non_trading_day"),
    ({"calendar": session(trading_date=date(2026, 11, 5),
                          opens_at=datetime(2026, 11, 5, 14, 30, tzinfo=timezone.utc),
                          closes_at=datetime(2026, 11, 5, 21, tzinfo=timezone.utc))},
     "calendar_date_mismatch"),
    ({"calendar": session(available_at=datetime(2026, 11, 4, 13, 1, tzinfo=timezone.utc))},
     "calendar_after_cutoff"),
    ({"universe": universe(effective_until=date(2026, 11, 4))},
     "universe_not_effective"),
    ({"universe": universe(available_at=datetime(2026, 11, 4, 13, 1, tzinfo=timezone.utc))},
     "universe_after_cutoff"),
])
def test_manifest_requires_an_effective_known_trading_context(changes, reason):
    result = manifest(**({"calendar": session(), "universe": universe()} | changes))
    assert result.availability_state == "withheld"
    assert reason in result.unavailable_reasons


@pytest.mark.parametrize("field", ["company_id", "ticker", "rank"])
def test_universe_requires_fifty_distinct_company_ticker_rank_mappings(field):
    members = list(universe().members)
    replacement = members[-1].model_dump() | {field: getattr(members[0], field)}
    members[-1] = CompanyTicker(**replacement)
    with pytest.raises(ValidationError, match="unique"):
        universe(members=tuple(members))


@pytest.mark.parametrize("changes", [
    {"closes_at": None},
    {"closes_at": datetime(2026, 11, 4, 14, tzinfo=timezone.utc)},
    {"closes_at": datetime(2026, 11, 5, 21, tzinfo=timezone.utc)},
    {"is_trading_day": False},
])
def test_malformed_exchange_session_is_rejected(changes):
    with pytest.raises(ValidationError, match="session"):
        session(**changes)


@pytest.mark.parametrize("changes", [
    {"effective_until": date(2026, 11, 3)},
    {"ranked_at": datetime(2026, 11, 4, 12, tzinfo=timezone.utc)},
])
def test_universe_rejects_invalid_effective_interval_or_timestamp_order(changes):
    with pytest.raises(ValidationError):
        universe(**changes)


def test_manifest_cannot_bypass_the_evidence_availability_gate():
    with pytest.raises(ValidationError, match="eligible"):
        manifest(evidence=(evidence(available_at=None),))


def test_manifest_has_an_explicit_cutoff_and_a_replayable_content_hash():
    original = manifest(calendar=session(), universe=universe())
    assert original.cutoff == publication_cutoff(original.trading_date)
    encoded = original.canonical_json()
    assert original.manifest_hash == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert len(original.manifest_hash) == 64
    restored = PublicationManifest.model_validate_json(encoded)
    assert restored == original
    assert restored.manifest_hash == original.manifest_hash


def test_future_versions_and_retries_do_not_change_the_original_manifest_hash():
    cutoff = publication_cutoff(date(2026, 11, 4))
    original = evidence()
    future = evidence(
        "future", content_hash="b" * 64,
        available_at=datetime(2026, 11, 4, 14, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 11, 4, 14, 1, tzinfo=timezone.utc),
    )
    before = manifest(evidence=select_evidence([original], cutoff).selected,
                      calendar=session(), universe=universe())
    after = manifest(evidence=select_evidence([future, original, original], cutoff).selected,
                     calendar=session(), universe=universe(
                         members=tuple(reversed(universe().members))))
    assert before.manifest_hash == after.manifest_hash
    revised = manifest(evidence=(evidence("revised", content_hash="d" * 64),),
                       calendar=session(), universe=universe())
    assert revised.manifest_hash != before.manifest_hash


def test_half_day_keeps_the_cutoff_and_an_early_open_withholds():
    half_day = session(closes_at=datetime(2026, 11, 4, 18, tzinfo=timezone.utc))
    result = manifest(calendar=half_day, universe=universe())
    assert result.cutoff == publication_cutoff(result.trading_date)
    assert result.availability_state == "eligible_inputs"
    early_open = session(opens_at=result.cutoff)
    refused = manifest(calendar=early_open, universe=universe())
    assert refused.availability_state == "withheld"
    assert "cutoff_not_before_session" in refused.unavailable_reasons


@pytest.mark.parametrize("field", ["source", "version", "policy_reference",
                                   "share_class_policy", "rebalance_policy"])
def test_blank_universe_provenance_is_not_a_completed_reference(field):
    with pytest.raises(ValidationError):
        universe(**{field: "   "})


def test_manifest_rejects_a_tampered_cutoff_and_preserves_frozen_original():
    with pytest.raises(ValidationError, match="08:00"):
        manifest(cutoff=datetime(2026, 11, 4, 14, tzinfo=timezone.utc))
    original = manifest(calendar=session(), universe=universe())
    original_hash = original.manifest_hash
    with pytest.raises(ValidationError, match="frozen"):
        original.universe.members[0].ticker = "CHANGED"
    copy = original.model_dump(mode="json")
    copy["evidence"][0]["content_hash"] = "e" * 64
    assert original.manifest_hash == original_hash
    with pytest.raises(ValidationError):
        universe(members=universe().members[:49])
    with pytest.raises(ValidationError):
        CompanyTicker(company_id="synthetic", ticker="SYN", country="MY", rank=1)
