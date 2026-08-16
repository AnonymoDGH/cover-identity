"""Tests for cover_identity.digital_footprint -- on-legend online presence."""

from __future__ import annotations

import datetime as dt
import random

from cover_identity import digital_footprint as fp
from cover_identity import generate

TODAY = dt.date(2024, 6, 1)


def _ident():
    return generate(seed=42)


def test_footprint_deterministic():
    ident = _ident()
    a = fp.build_footprint(ident, seed=3, today=TODAY)
    b = fp.build_footprint(ident, seed=3, today=TODAY)
    assert a == b


def test_profiles_not_predating_adulthood():
    ident = _ident()
    profiles = fp.make_profiles(ident, random.Random(1), today=TODAY)
    dob = dt.date.fromisoformat(ident["date_of_birth"])
    for p in profiles:
        created = dt.date.fromisoformat(p["created"])
        assert created > dob


def test_profiles_handle_echoes_name():
    ident = _ident()
    profiles = fp.make_profiles(ident, random.Random(2), today=TODAY)
    first = ident["name"].split()[0].lower()
    for p in profiles:
        assert p["handle"].startswith(first)


def test_posts_sorted_and_on_legend():
    ident = _ident()
    posts = fp.make_posts(ident, random.Random(3), count=6, today=TODAY)
    dates = [p["date"] for p in posts]
    assert dates == sorted(dates)
    # Work posts mention the occupation.
    work_posts = [p for p in posts if p["category"] == "work"]
    for p in work_posts:
        assert ident["occupation"] in p["text"]


def test_forum_activity_uses_known_skills():
    ident = _ident()
    from cover_identity import corpus
    activity = fp.make_forum_activity(ident, random.Random(4), count=3)
    for a in activity:
        skill = a["topic"].replace("Getting started with ", "")
        assert skill in corpus.SKILLS


def test_footprint_report_shape():
    ident = _ident()
    footprint = fp.build_footprint(ident, seed=5, today=TODAY)
    report = fp.footprint_report(footprint)
    assert report["platforms"] == len(footprint["profiles"])
    assert report["posts"] == len(footprint["posts"])
    assert report["forum_threads"] == len(footprint["forum_activity"])


def test_young_cover_has_fewer_profiles():
    # A very young identity should have few or no accounts.
    young = generate(seed=1)
    young["date_of_birth"] = "2012-01-01"
    profiles = fp.make_profiles(young, random.Random(1), today=TODAY)
    assert len(profiles) == 0
