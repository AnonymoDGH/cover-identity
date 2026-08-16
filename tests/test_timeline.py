"""Tests for cover_identity.timeline -- dated life history."""

from __future__ import annotations

import datetime as dt
import random

from cover_identity import timeline as tl


DOB = dt.date(1985, 3, 14)
TODAY = dt.date(2024, 6, 1)


def test_timeline_is_chronological():
    events = tl.build_timeline(DOB, "locksmith", random.Random(1), today=TODAY)
    years = [e["year"] for e in events]
    assert years == sorted(years)


def test_timeline_starts_with_birth():
    events = tl.build_timeline(DOB, "locksmith", random.Random(1), today=TODAY)
    assert events[0]["event"] == "born"
    assert events[0]["year"] == DOB.year


def test_timeline_ends_with_present():
    events = tl.build_timeline(DOB, "locksmith", random.Random(1), today=TODAY)
    assert events[-1]["event"] == "present"
    assert "locksmith" in events[-1]["detail"]


def test_timeline_deterministic():
    a = tl.build_timeline(DOB, "archivist", random.Random(7), today=TODAY)
    b = tl.build_timeline(DOB, "archivist", random.Random(7), today=TODAY)
    assert a == b


def test_no_future_events():
    events = tl.build_timeline(DOB, "translator", random.Random(2), today=TODAY)
    assert all(e["year"] <= TODAY.year for e in events)


def test_young_cover_has_fewer_events():
    young_dob = dt.date(2010, 1, 1)
    events = tl.build_timeline(young_dob, "barista trainer",
                               random.Random(3), today=TODAY)
    # A 14-year-old should not have relocation/training/present-work events.
    kinds = {e["event"] for e in events}
    assert "relocation" not in kinds


def test_year_of_age():
    assert tl.year_of_age(DOB, 10) == 1995


def test_timeline_to_text():
    events = tl.build_timeline(DOB, "locksmith", random.Random(1), today=TODAY)
    text = tl.timeline_to_text(events)
    assert str(DOB.year) in text
    assert "born" in text


def test_gap_report_detects_large_gap():
    timeline = [
        {"year": 1990, "event": "a"},
        {"year": 2005, "event": "b"},
    ]
    gaps = tl.gap_report(timeline, max_gap=8)
    assert gaps == [{"from_year": 1990, "to_year": 2005, "years": 15}]


def test_gap_report_empty_when_tight():
    timeline = [{"year": 2000}, {"year": 2003}]
    assert tl.gap_report(timeline, max_gap=8) == []
