"""Tests for cover_identity.personas -- archetype templates."""

from __future__ import annotations

import pytest

from cover_identity import corpus
from cover_identity import generate
from cover_identity import personas


def test_list_personas():
    names = personas.list_personas()
    assert "tradesperson" in names
    assert names == sorted(names)


def test_get_persona():
    p = personas.get_persona("clerk")
    assert p["sector"] == "logistics"


def test_get_unknown_persona_raises():
    with pytest.raises(personas.PersonaError):
        personas.get_persona("nonexistent")


def test_apply_persona_sets_sector_occupation():
    ident = generate(seed=42)
    result = personas.apply_persona(ident, "tradesperson", seed=1)
    assert result["occupation"] in corpus.OCCUPATIONS["trades"]


def test_apply_persona_does_not_mutate_input():
    ident = generate(seed=42)
    before = dict(ident)
    personas.apply_persona(ident, "creative", seed=1)
    assert ident == before


def test_apply_persona_adds_hobbies_and_metadata():
    ident = generate(seed=42)
    result = personas.apply_persona(ident, "scholar", seed=2)
    assert len(result["hobbies"]) == 2
    assert result["persona"]["name"] == "scholar"
    assert result["persona"]["footprint_loudness"] == "low"


def test_apply_persona_deterministic():
    ident = generate(seed=42)
    a = personas.apply_persona(ident, "host", seed=5)
    b = personas.apply_persona(ident, "host", seed=5)
    assert a == b


def test_network_size_for():
    assert personas.network_size_for("small") == 3
    assert personas.network_size_for("large") == 8
    assert personas.network_size_for("unknown") == 5


def test_every_persona_sector_is_valid():
    for name in personas.list_personas():
        p = personas.get_persona(name)
        assert p["sector"] in corpus.OCCUPATIONS
