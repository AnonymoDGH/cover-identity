"""Tests for cover_identity.comms -- check-in schedule and escalation."""

from __future__ import annotations

import random

import pytest

from cover_identity import comms


def test_build_schedule_deterministic():
    a = comms.build_schedule(random.Random(1), per_week=3)
    b = comms.build_schedule(random.Random(1), per_week=3)
    assert a == b


def test_build_schedule_distinct_days():
    schedule = comms.build_schedule(random.Random(2), per_week=4)
    days = [c.day for c in schedule]
    assert len(days) == len(set(days)) == 4


def test_build_schedule_clamped_to_week():
    schedule = comms.build_schedule(random.Random(3), per_week=99)
    assert len(schedule) == 7


def test_build_schedule_min():
    with pytest.raises(comms.CommsError):
        comms.build_schedule(random.Random(1), per_week=0)


def test_checkin_has_distinct_channels():
    schedule = comms.build_schedule(random.Random(4), per_week=3)
    for c in schedule:
        assert c.channel != c.backup_channel


def test_escalation_ladder_monotonic():
    levels = [comms.escalation_for_missed(i)["level"] for i in range(4)]
    assert levels == ["normal", "watch", "concern", "alarm"]


def test_escalation_caps_at_alarm():
    assert comms.escalation_for_missed(99)["level"] == "alarm"


def test_escalation_negative():
    with pytest.raises(comms.CommsError):
        comms.escalation_for_missed(-1)


def test_log_consecutive_misses():
    log = comms.CommsLog()
    log.record("Mon", scheduled=True, made=True)
    log.record("Wed", scheduled=True, made=False)
    log.record("Fri", scheduled=True, made=False)
    assert log.consecutive_misses() == 2


def test_log_miss_streak_resets_on_contact():
    log = comms.CommsLog()
    log.record("Mon", scheduled=True, made=False)
    log.record("Wed", scheduled=True, made=True)
    assert log.consecutive_misses() == 0


def test_log_ignores_unscheduled():
    log = comms.CommsLog()
    log.record("Mon", scheduled=False, made=False)
    assert log.consecutive_misses() == 0


def test_log_current_escalation():
    log = comms.CommsLog()
    for day in ("Mon", "Wed", "Fri"):
        log.record(day, scheduled=True, made=False)
    assert log.current_escalation()["level"] == "alarm"


def test_log_contact_rate():
    log = comms.CommsLog()
    log.record("Mon", scheduled=True, made=True)
    log.record("Wed", scheduled=True, made=False)
    assert log.contact_rate() == 0.5


def test_log_contact_rate_no_scheduled():
    log = comms.CommsLog()
    log.record("Mon", scheduled=False, made=False)
    assert log.contact_rate() == 1.0
