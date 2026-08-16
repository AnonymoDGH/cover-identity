"""Tests for cover_identity.scenarios -- rehearsal scenarios."""

from __future__ import annotations

from cover_identity import generate
from cover_identity import scenarios as sc


def _ident():
    return generate(seed=42)


def test_build_scenarios_deterministic():
    ident = _ident()
    a = sc.build_scenarios(ident, seed=1, count=3)
    b = sc.build_scenarios(ident, seed=1, count=3)
    assert a == b


def test_build_scenarios_count_clamped():
    ident = _ident()
    assert len(sc.build_scenarios(ident, seed=1, count=99)) == len(sc._BUILDERS)
    assert len(sc.build_scenarios(ident, seed=1, count=0)) == 1


def test_scenario_titles_unique():
    ident = _ident()
    scenarios = sc.build_scenarios(ident, seed=2, count=5)
    titles = [s.title for s in scenarios]
    assert len(titles) == len(set(titles))


def test_scenario_fields_populated():
    ident = _ident()
    for scenario in sc.build_scenarios(ident, seed=3, count=5):
        assert scenario.title
        assert scenario.setting
        assert scenario.other_person
        assert scenario.opening_line
        assert scenario.exercises


def test_scenario_to_text():
    ident = _ident()
    scenario = sc.build_scenarios(ident, seed=4, count=1)[0]
    text = sc.scenario_to_text(scenario)
    assert "SCENARIO:" in text
    assert scenario.title in text
    assert "opens:" in text
