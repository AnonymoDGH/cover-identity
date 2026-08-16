"""Tests for cover_identity.emergency -- duress codes and protocols."""

from __future__ import annotations

import random

import pytest

from cover_identity import emergency as em


def test_build_duress_codes_deterministic():
    a = em.build_duress_codes(random.Random(1), count=3)
    b = em.build_duress_codes(random.Random(1), count=3)
    assert a == b


def test_duress_codes_unique():
    codes = em.build_duress_codes(random.Random(2), count=4)
    assert em.verify_duress_codes(codes) == []


def test_duress_codes_clamped():
    codes = em.build_duress_codes(random.Random(3), count=99)
    assert len(codes) == len(em._MEANINGS)


def test_duress_codes_min():
    with pytest.raises(em.EmergencyError):
        em.build_duress_codes(random.Random(1), count=0)


def test_verify_flags_duplicate_phrase():
    codes = [
        em.DuressCode("the weather turned cold", "meaning a", "spoken"),
        em.DuressCode("the weather turned cold", "meaning b", "spoken"),
    ]
    problems = em.verify_duress_codes(codes)
    assert any("same phrase" in p for p in problems)


def test_verify_flags_duplicate_meaning():
    codes = [
        em.DuressCode("phrase one here", "same meaning", "spoken"),
        em.DuressCode("phrase two here", "same meaning", "spoken"),
    ]
    problems = em.verify_duress_codes(codes)
    assert any("same meaning" in p for p in problems)


def test_verify_flags_short_phrase():
    codes = [em.DuressCode("hi", "meaning", "spoken")]
    problems = em.verify_duress_codes(codes)
    assert any("too short" in p for p in problems)


def test_emergency_protocol_ordered():
    steps = em.build_emergency_protocol()
    orders = [s.order for s in steps]
    assert orders == list(range(1, len(steps) + 1))


def test_protocol_to_text():
    steps = em.build_emergency_protocol()
    text = em.protocol_to_text(steps)
    assert "EMERGENCY PROTOCOL" in text
    assert "1." in text
    assert str(len(steps)) + "." in text


def test_every_step_has_action_and_window():
    for step in em.build_emergency_protocol():
        assert step.action
        assert step.within
