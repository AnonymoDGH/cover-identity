"""Tests for cover_identity.rotation -- legend lifecycle scheduling."""

from __future__ import annotations

import datetime as dt

import pytest

from cover_identity import rotation as rot

TODAY = dt.date(2024, 6, 1)


def _schedule():
    s = rot.RotationSchedule()
    s.register("berlin")
    s.register("oslo")
    return s


def test_register_and_names():
    s = _schedule()
    assert s.names() == ["berlin", "oslo"]
    assert len(s) == 2


def test_register_duplicate_rejected():
    s = _schedule()
    with pytest.raises(rot.RotationError):
        s.register("berlin")


def test_register_empty_rejected():
    s = rot.RotationSchedule()
    with pytest.raises(rot.RotationError):
        s.register("   ")


def test_activate_sets_expiry():
    s = _schedule()
    slot = s.activate("berlin", TODAY)
    assert slot.status == rot.Status.ACTIVE
    assert slot.activated == TODAY
    assert slot.expires == TODAY + dt.timedelta(days=rot.DEFAULT_HORIZON_DAYS)
    assert slot.runs == 1


def test_only_one_active_at_a_time():
    s = _schedule()
    s.activate("berlin", TODAY)
    with pytest.raises(rot.RotationError):
        s.activate("oslo", TODAY)


def test_burned_legend_cannot_activate():
    s = _schedule()
    s.burn("berlin")
    with pytest.raises(rot.RotationError):
        s.activate("berlin", TODAY)


def test_retire_then_activate_other():
    s = _schedule()
    s.activate("berlin", TODAY)
    s.retire("berlin")
    s.activate("oslo", TODAY)
    assert s.active().name == "oslo"


def test_retire_nonactive_rejected():
    s = _schedule()
    with pytest.raises(rot.RotationError):
        s.retire("berlin")


def test_next_runnable_prefers_fresh():
    s = _schedule()
    s.activate("berlin", TODAY)
    s.retire("berlin")  # berlin now has 1 run
    nxt = s.next_runnable()
    assert nxt.name == "oslo"  # oslo has 0 runs


def test_next_runnable_none_when_all_burned():
    s = _schedule()
    s.burn("berlin")
    s.burn("oslo")
    assert s.next_runnable() is None


def test_due_for_rotation():
    s = _schedule()
    s.activate("berlin", TODAY, horizon_days=10)
    assert s.due_for_rotation(TODAY) == []
    due = s.due_for_rotation(TODAY + dt.timedelta(days=11))
    assert [x.name for x in due] == ["berlin"]


def test_default_horizon():
    assert rot.default_horizon_days() == 180


def test_effective_horizon_clean():
    assert rot.effective_horizon_days(0, 0.0) == rot.DEFAULT_HORIZON_DAYS


def test_effective_horizon_penalized():
    clean = rot.effective_horizon_days(0, 0.0)
    dirty = rot.effective_horizon_days(2, 0.5)
    assert dirty < clean


def test_effective_horizon_floor():
    assert rot.effective_horizon_days(100, 1.0) == 30


def test_effective_horizon_validation():
    with pytest.raises(rot.RotationError):
        rot.effective_horizon_days(-1, 0.0)
    with pytest.raises(rot.RotationError):
        rot.effective_horizon_days(0, 1.5)
