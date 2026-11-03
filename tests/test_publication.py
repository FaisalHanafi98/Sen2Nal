"""Synthetic publication inputs; no exchange/provider/database access."""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from src.contracts.publication import EvidenceVersion, publication_cutoff, select_evidence


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
