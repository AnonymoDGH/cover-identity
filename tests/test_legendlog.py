"""Tests for cover_identity.legendlog -- legend versioning."""

from __future__ import annotations

import pytest

from cover_identity import legendlog as ll


def _log():
    log = ll.LegendLog("berlin")
    log.change("address", "1 Main St", "4 Canal Rd", "landlord sold the building")
    log.change("phone", "555-0100", "555-0200", "old number got spam calls")
    return log


def test_requires_name():
    with pytest.raises(ll.LegendLogError):
        ll.LegendLog("   ")


def test_version_bumps():
    log = _log()
    assert log.version == 3  # started at 1, two changes


def test_identical_change_rejected():
    log = ll.LegendLog("berlin")
    with pytest.raises(ll.LegendLogError):
        log.change("address", "same", "same", "reason")


def test_empty_reason_rejected():
    log = ll.LegendLog("berlin")
    with pytest.raises(ll.LegendLogError):
        log.change("address", "a", "b", "   ")


def test_empty_field_rejected():
    log = ll.LegendLog("berlin")
    with pytest.raises(ll.LegendLogError):
        log.change("  ", "a", "b", "reason")


def test_fields_changed_order():
    log = _log()
    assert log.fields_changed() == ["address", "phone"]


def test_fields_changed_dedupes():
    log = _log()
    log.change("address", "4 Canal Rd", "9 Hill St", "moved again")
    assert log.fields_changed() == ["address", "phone"]


def test_latest_for():
    log = _log()
    log.change("address", "4 Canal Rd", "9 Hill St", "moved again")
    latest = log.latest_for("address")
    assert latest.new_value == "9 Hill St"


def test_latest_for_missing():
    log = _log()
    assert log.latest_for("email") is None


def test_memorize_list_current_values():
    log = _log()
    log.change("address", "4 Canal Rd", "9 Hill St", "moved again")
    lines = log.memorize_list()
    assert "address: 9 Hill St" in lines
    assert "phone: 555-0200" in lines
    assert len(lines) == 2


def test_to_text():
    log = _log()
    text = log.to_text()
    assert "LEGEND LOG: berlin" in text
    assert "v2" in text and "v3" in text
    assert "landlord sold the building" in text


def test_len():
    log = _log()
    assert len(log) == 2
