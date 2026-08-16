"""Tests for cover_identity.alibi -- alibi construction and verification."""

from __future__ import annotations

import random

import pytest

from cover_identity import alibi as al
from cover_identity import habits as hb


def _blocks():
    return hb.build_routine(random.Random(1), "locksmith")


def test_claim_from_routine_matches_block():
    blocks = _blocks()
    claim = al.claim_from_routine(blocks, 10)
    block = hb.where_at(blocks, 10)
    assert claim.place == block.location
    assert claim.activity == block.activity


def test_claim_from_routine_no_block():
    blocks = _blocks()
    with pytest.raises(al.AlibiError):
        al.claim_from_routine(blocks, 3)  # asleep, no block


def test_claim_invalid_hour():
    with pytest.raises(al.AlibiError):
        al.AlibiClaim(hour=25, place="x", activity="y")


def test_build_alibi_sorted():
    blocks = _blocks()
    a = al.build_alibi("Tuesday", blocks, [14, 10, 12])
    assert a.hours_covered() == [10, 12, 14]


def test_build_alibi_with_witness():
    blocks = _blocks()
    a = al.build_alibi("Tuesday", blocks, [10], witnesses={10: "Mara Keller"})
    assert a.claims[0].witness == "Mara Keller"


def test_duplicate_hour_rejected():
    blocks = _blocks()
    a = al.Alibi(day="Tuesday")
    a.add(al.claim_from_routine(blocks, 10))
    with pytest.raises(al.AlibiError):
        a.add(al.claim_from_routine(blocks, 10))


def test_verify_clean_alibi():
    blocks = _blocks()
    a = al.build_alibi("Tuesday", blocks, [10, 14, 18])
    assert al.verify_alibi(a, blocks) == []


def test_verify_flags_place_contradiction():
    blocks = _blocks()
    a = al.Alibi(day="Tuesday")
    a.add(al.AlibiClaim(hour=10, place="the beach", activity="swimming"))
    problems = al.verify_alibi(a, blocks)
    assert any("routine" in p for p in problems)


def test_verify_flags_unknown_witness():
    blocks = _blocks()
    network = [{"name": "Mara Keller"}]
    a = al.Alibi(day="Tuesday")
    a.add(al.AlibiClaim(hour=10, place=hb.where_at(blocks, 10).location,
                        activity="work", witness="Nobody Here"))
    problems = al.verify_alibi(a, blocks, network)
    assert any("not in the network" in p for p in problems)


def test_verify_known_witness_ok():
    blocks = _blocks()
    network = [{"name": "Mara Keller"}]
    a = al.Alibi(day="Tuesday")
    a.add(al.AlibiClaim(hour=10, place=hb.where_at(blocks, 10).location,
                        activity="work", witness="Mara Keller"))
    assert al.verify_alibi(a, blocks, network) == []


def test_alibi_to_text():
    blocks = _blocks()
    a = al.build_alibi("Tuesday", blocks, [10])
    text = al.alibi_to_text(a)
    assert "ALIBI FOR TUESDAY" in text
    assert "10:00" in text
