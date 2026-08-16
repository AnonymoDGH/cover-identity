"""Tests for cover_identity.aliases -- alias graph and cross-checks."""

from __future__ import annotations

import pytest

from cover_identity import generate
from cover_identity.aliases import Alias, AliasError, AliasGraph, from_identity


def _alias(name, **fields):
    return Alias(name=name, context="test", fields=fields)


def test_add_and_get():
    g = AliasGraph()
    g.add(_alias("berlin", phone="555-0100"))
    assert g.get("berlin").name == "berlin"
    assert len(g) == 1


def test_duplicate_name_rejected():
    g = AliasGraph()
    g.add(_alias("berlin"))
    with pytest.raises(AliasError):
        g.add(_alias("berlin"))


def test_empty_name_rejected():
    g = AliasGraph()
    with pytest.raises(AliasError):
        g.add(_alias("   "))


def test_get_missing_raises():
    g = AliasGraph()
    with pytest.raises(AliasError):
        g.get("ghost")


def test_retire_keeps_but_deactivates():
    g = AliasGraph()
    g.add(_alias("berlin"))
    g.retire("berlin")
    assert g.get("berlin").active is False
    assert g.names(active_only=True) == []
    assert g.names() == ["berlin"]


def test_cross_check_detects_shared_phone():
    g = AliasGraph()
    g.add(_alias("berlin", phone="555-0100"))
    g.add(_alias("oslo", phone="555-0100"))
    collisions = g.cross_check()
    assert len(collisions) == 1
    assert collisions[0]["field"] == "phone"
    assert collisions[0]["aliases"] == ["berlin", "oslo"]


def test_cross_check_ignores_retired():
    g = AliasGraph()
    g.add(_alias("berlin", phone="555-0100"))
    g.add(_alias("oslo", phone="555-0100"))
    g.retire("berlin")
    assert g.cross_check() == []


def test_cross_check_clean_when_distinct():
    g = AliasGraph()
    g.add(_alias("berlin", phone="555-0100", email="b@x.com"))
    g.add(_alias("oslo", phone="555-0200", email="o@x.com"))
    assert g.cross_check() == []


def test_separation_report():
    g = AliasGraph()
    g.add(_alias("berlin", address="1 Main St"))
    g.add(_alias("oslo", address="1 Main St"))
    report = g.separation_report()
    assert report["active_aliases"] == 2
    assert report["collisions"] == 1
    assert report["clean"] is False


def test_from_identity_pulls_collision_fields():
    ident = generate(seed=42)
    alias = from_identity("berlin", "deep cover", ident)
    assert alias.name == "berlin"
    assert alias.fields["email"] == ident["email"]
    assert alias.fields["phone"] == ident["phone"]
    assert "name" not in alias.fields  # only collision fields


def test_generated_identities_do_not_collide():
    # Two different seeds should produce non-colliding contact fields.
    a = from_identity("a", "x", generate(seed=1))
    b = from_identity("b", "y", generate(seed=2))
    g = AliasGraph()
    g.add(a)
    g.add(b)
    assert g.cross_check() == []
