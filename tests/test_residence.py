"""Tests for cover_identity.residence -- home, safe houses, neighborhood."""

from __future__ import annotations

import random

import pytest

from cover_identity import residence as res


def test_build_residence_deterministic():
    a = res.build_residence(random.Random(1), "12 Mill Lane")
    b = res.build_residence(random.Random(1), "12 Mill Lane")
    assert a == b


def test_build_residence_shape():
    r = res.build_residence(random.Random(2), "12 Mill Lane")
    assert r.address == "12 Mill Lane"
    assert r.dwelling_type in res._DWELLINGS
    assert r.how_long in res._HOW_LONG
    assert r.landlord_story in res._LANDLORD


def test_build_residence_empty_address():
    with pytest.raises(res.ResidenceError):
        res.build_residence(random.Random(1), "   ")


def test_build_safe_houses_distinct_purposes():
    houses = res.build_safe_houses(random.Random(3), count=3)
    purposes = [h.purpose for h in houses]
    assert len(purposes) == len(set(purposes))
    assert len(houses) == 3


def test_build_safe_houses_clamps():
    houses = res.build_safe_houses(random.Random(4), count=99)
    assert len(houses) == len(res._PURPOSES)


def test_build_safe_houses_min():
    with pytest.raises(res.ResidenceError):
        res.build_safe_houses(random.Random(1), count=0)


def test_safe_house_ids_sequential():
    houses = res.build_safe_houses(random.Random(5), count=3)
    assert [h.site_id for h in houses] == ["safe-1", "safe-2", "safe-3"]


def test_build_neighborhood_facts():
    n = res.build_neighborhood(random.Random(6))
    facts = n.facts()
    assert len(facts) == 5
    assert all(f.endswith(".") for f in facts)
    assert n.pub_name in res._PUBS


def test_neighborhood_deterministic():
    a = res.build_neighborhood(random.Random(7))
    b = res.build_neighborhood(random.Random(7))
    assert a == b


def test_residence_brief_contains_sections():
    r = res.build_residence(random.Random(8), "12 Mill Lane")
    houses = res.build_safe_houses(random.Random(8), count=2)
    n = res.build_neighborhood(random.Random(8))
    brief = res.residence_brief(r, houses, n)
    assert "HOME:" in brief
    assert "NEIGHBORHOOD:" in brief
    assert "SAFE HOUSES:" in brief
    assert "12 Mill Lane" in brief
