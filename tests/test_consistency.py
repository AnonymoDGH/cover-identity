"""Tests for cover_identity.consistency -- legend auditing."""

from __future__ import annotations

import datetime as dt

from cover_identity import consistency as cons
from cover_identity import generate


def _good_identity():
    ident = generate(seed=42)
    return ident


def test_generated_identity_is_clean():
    ident = _good_identity()
    findings = cons.audit(ident)
    errors = [f for f in findings if f.severity == cons.Severity.ERROR]
    assert errors == [], [str(f) for f in errors]


def test_age_mismatch_flagged():
    ident = _good_identity()
    ident["age"] = ident["age"] + 5
    findings = cons.check_age_dob(ident)
    assert any(f.severity == cons.Severity.ERROR for f in findings)


def test_bad_dob_flagged():
    ident = _good_identity()
    ident["date_of_birth"] = "not-a-date"
    findings = cons.check_age_dob(ident)
    assert any("unparseable" in f.message for f in findings)


def test_email_without_at_flagged():
    findings = cons.check_email_name({"email": "nope", "name": "Ada Lovelace"})
    assert any(f.severity == cons.Severity.ERROR for f in findings)


def test_email_echoing_name_ok():
    findings = cons.check_email_name(
        {"email": "ada.lovelace@example.com", "name": "Ada Lovelace"})
    assert findings == []


def test_phone_digit_count():
    assert cons.check_phone_shape({"phone": "123"}) != []
    assert cons.check_phone_shape({"phone": "+1 (555) 010-2345"}) == []


def test_backstory_missing_name_flagged():
    findings = cons.check_backstory_names(
        {"backstory": "A person lived quietly.", "name": "Zelda Quinn"})
    assert any("first name" in f.message for f in findings)


def test_empty_anchor_answer_flagged():
    ident = {"cover_questions": [{"question": "pet", "answer": "  "}]}
    findings = cons.check_anchors_present(ident)
    assert any(f.severity == cons.Severity.ERROR for f in findings)


def test_timeline_future_event_flagged():
    today = dt.date(2024, 6, 1)
    ident = {
        "date_of_birth": "1990-01-01",
        "timeline": [{"year": 2030, "event": "x"}],
    }
    findings = cons.check_timeline(ident, today=today)
    assert any("future" in f.message for f in findings)


def test_timeline_out_of_order_flagged():
    ident = {
        "date_of_birth": "1990-01-01",
        "timeline": [{"year": 2010}, {"year": 2005}],
    }
    findings = cons.check_timeline(ident)
    assert any("chronological" in f.message for f in findings)


def test_worst_severity():
    findings = [
        cons.Finding("a", cons.Severity.INFO, "x"),
        cons.Finding("b", cons.Severity.ERROR, "y"),
    ]
    assert cons.worst_severity(findings) == cons.Severity.ERROR
    assert cons.worst_severity([]) is None


def test_finding_str():
    f = cons.Finding("age", cons.Severity.WARN, "off by one")
    assert "[WARN] age: off by one" == str(f)
