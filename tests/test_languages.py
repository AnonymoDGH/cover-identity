"""Tests for cover_identity.languages -- language and accent layer."""

from __future__ import annotations

import random

import pytest

from cover_identity import languages as lang


def test_build_profile_deterministic():
    a = lang.build_language_profile(random.Random(1), extra_languages=2)
    b = lang.build_language_profile(random.Random(1), extra_languages=2)
    assert a == b


def test_native_always_present():
    p = lang.build_language_profile(random.Random(2), extra_languages=0)
    natives = [s for s in p.skills if s.level == "native"]
    assert len(natives) == 1
    assert natives[0].language == p.native


def test_extras_never_native():
    p = lang.build_language_profile(random.Random(3), extra_languages=3)
    for skill in p.skills:
        if skill.language != p.native:
            assert skill.level != "native"


def test_extra_count_clamped():
    p = lang.build_language_profile(random.Random(4), extra_languages=99)
    assert len(p.skills) == len(lang._LANGUAGES)


def test_negative_extras_rejected():
    with pytest.raises(lang.LanguagesError):
        lang.build_language_profile(random.Random(1), extra_languages=-1)


def test_invalid_proficiency_rejected():
    with pytest.raises(lang.LanguagesError):
        lang.LanguageSkill(language="x", level="godlike")


def test_strongest_non_native():
    p = lang.LanguageProfile(
        native="a", accent="b",
        skills=[
            lang.LanguageSkill("a", "native"),
            lang.LanguageSkill("b", "conversational"),
            lang.LanguageSkill("c", "fluent"),
        ])
    assert p.strongest().language == "c"


def test_strongest_none_when_only_native():
    p = lang.LanguageProfile(native="a", accent="b",
                             skills=[lang.LanguageSkill("a", "native")])
    assert p.strongest() is None


def test_local_phrases():
    phrases = lang.local_phrases(random.Random(5), count=3)
    assert len(phrases) == 3
    assert len(set(phrases)) == 3


def test_local_phrases_min():
    with pytest.raises(lang.LanguagesError):
        lang.local_phrases(random.Random(1), count=0)


def test_profile_to_text():
    p = lang.build_language_profile(random.Random(6), extra_languages=1)
    phrases = lang.local_phrases(random.Random(6), count=2)
    text = lang.profile_to_text(p, phrases)
    assert "LANGUAGE PROFILE" in text
    assert p.native in text
    assert p.accent in text
