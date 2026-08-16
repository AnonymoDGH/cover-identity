"""Tests for cover_identity.medical -- cover medical history."""

from __future__ import annotations

import random

import pytest

from cover_identity import medical as med


def test_build_profile_deterministic():
    a = med.build_medical_profile(random.Random(1), 40)
    b = med.build_medical_profile(random.Random(1), 40)
    assert a == b


def test_blood_type_is_valid():
    p = med.build_medical_profile(random.Random(2), 35)
    assert p.blood_type in med.BLOOD_TYPES


def test_allergies_nonempty_and_no_none_with_others():
    p = med.build_medical_profile(random.Random(3), 30)
    assert p.allergies
    if "none known" in p.allergies:
        assert p.allergies == ["none known"]


def test_last_checkup_not_future():
    p = med.build_medical_profile(random.Random(4), 45, today_year=2024)
    assert int(p.last_checkup) <= 2024


def test_negative_age_rejected():
    with pytest.raises(med.MedicalError):
        med.build_medical_profile(random.Random(1), -1)


def test_summary_mentions_blood():
    p = med.build_medical_profile(random.Random(5), 40)
    assert p.blood_type in p.summary()


def test_medical_card_contains_fields():
    p = med.build_medical_profile(random.Random(6), 40)
    card = med.medical_card(p, "Ada Lovelace", "1985-03-14")
    assert "MEDICAL CARD" in card
    assert "Ada Lovelace" in card
    assert "1985-03-14" in card
    assert p.blood_type in card
    assert p.doctor_name in card
