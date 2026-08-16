"""Tests for cover_identity.debrief -- post-operation review."""

from __future__ import annotations

import pytest

from cover_identity import debrief as db


def _debrief():
    d = db.Debrief("berlin")
    d.add("Where do you live?", "address", db.Outcome.CLEAN)
    d.add("What's your mother's maiden name?", "mother_maiden", db.Outcome.SHAKY)
    d.add("Where were you in 2019?", "timeline", db.Outcome.INVENTED)
    return d


def test_debrief_requires_name():
    with pytest.raises(db.DebriefError):
        db.Debrief("   ")


def test_add_and_len():
    d = _debrief()
    assert len(d) == 3


def test_invalid_outcome_rejected():
    d = db.Debrief("berlin")
    with pytest.raises(db.DebriefError):
        d.add("q", "f", "spectacular")


def test_outcome_counts():
    d = _debrief()
    counts = d.outcome_counts()
    assert counts[db.Outcome.CLEAN] == 1
    assert counts[db.Outcome.SHAKY] == 1
    assert counts[db.Outcome.INVENTED] == 1
    assert counts[db.Outcome.AVOIDED] == 0


def test_trouble_fields_invented_first():
    d = _debrief()
    assert d.trouble_fields() == ["timeline", "mother_maiden"]


def test_trouble_fields_dedupes():
    d = db.Debrief("berlin")
    d.add("q1", "timeline", db.Outcome.INVENTED)
    d.add("q2", "timeline", db.Outcome.SHAKY)
    assert d.trouble_fields() == ["timeline"]


def test_lessons_clean():
    d = db.Debrief("berlin")
    d.add("q", "address", db.Outcome.CLEAN)
    report = db.lessons_report(d)
    assert report["recommendation"] == "legend held; keep it as is"


def test_lessons_patch():
    d = _debrief()  # 1 invented
    report = db.lessons_report(d)
    assert report["recommendation"].startswith("patch")


def test_lessons_rebuild():
    d = db.Debrief("berlin")
    for i in range(4):
        d.add(f"q{i}", f"field{i}", db.Outcome.INVENTED)
    report = db.lessons_report(d)
    assert report["recommendation"].startswith("rebuild")


def test_lessons_empty():
    d = db.Debrief("berlin")
    report = db.lessons_report(d)
    assert report["moments"] == 0
    assert "no data" in report["recommendation"]


def test_report_shape():
    d = _debrief()
    report = db.lessons_report(d)
    assert report["legend"] == "berlin"
    assert report["moments"] == 3
    assert set(report["counts"]) == set(db.Outcome.ALL)
