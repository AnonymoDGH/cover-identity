"""Tests for cover_identity.corpus -- embedded data and pickers."""

from __future__ import annotations

import random

from cover_identity import corpus


def test_occupations_grouped_and_flat():
    assert set(corpus.OCCUPATIONS) == {"trades", "logistics", "knowledge",
                                       "hospitality", "creative"}
    for group in corpus.OCCUPATIONS.values():
        assert group
    assert len(corpus.FLAT_OCCUPATIONS) == sum(
        len(g) for g in corpus.OCCUPATIONS.values())


def test_pick_is_deterministic():
    a = corpus.pick(random.Random(1), corpus.SKILLS)
    b = corpus.pick(random.Random(1), corpus.SKILLS)
    assert a == b


def test_pick_many_distinct_and_stable():
    rng = random.Random(3)
    chosen = corpus.pick_many(rng, corpus.HOBBIES, 4)
    assert len(chosen) == len(set(chosen)) == 4
    # Stable order: matches original list order.
    idx = [corpus.HOBBIES.index(c) for c in chosen]
    assert idx == sorted(idx)


def test_pick_many_clamps_to_pool():
    chosen = corpus.pick_many(random.Random(0), ["a", "b"], 10)
    assert chosen == ["a", "b"]


def test_occupation_for_age_returns_known():
    for age in (25, 38, 52):
        occ = corpus.occupation_for_age(random.Random(age), age)
        assert occ in corpus.FLAT_OCCUPATIONS


def test_hobby_pair_distinct():
    a, b = corpus.hobby_pair(random.Random(9))
    assert a != b
    assert a in corpus.HOBBIES and b in corpus.HOBBIES


def test_backstory_beats_have_all_sections():
    assert set(corpus.BACKSTORY_BEATS) == {
        "origin", "disruption", "trade", "reputation", "closer"}
    for section, options in corpus.BACKSTORY_BEATS.items():
        assert options, section


def test_anchor_questions_unique_keys():
    keys = [k for _, k in corpus.ANCHOR_QUESTIONS]
    assert len(keys) == len(set(keys))
