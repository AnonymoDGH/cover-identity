"""Tests for cover_identity.dossier -- complete dossier assembly."""

from __future__ import annotations

import datetime as dt

from cover_identity import dossier

TODAY = dt.date(2024, 6, 1)


def test_assemble_is_deterministic():
    a = dossier.assemble(seed=42, today=TODAY)
    b = dossier.assemble(seed=42, today=TODAY)
    assert a == b


def test_assemble_has_all_sections():
    d = dossier.assemble(seed=42, today=TODAY)
    for key in ("identity", "wallet", "network", "footprint",
                "drill", "consistency", "risk"):
        assert key in d


def test_assemble_with_persona():
    d = dossier.assemble(seed=42, persona="tradesperson", today=TODAY)
    assert d["persona"] == "tradesperson"
    assert d["identity"]["persona"]["name"] == "tradesperson"


def test_assemble_identity_is_consistent():
    d = dossier.assemble(seed=42, today=TODAY)
    errors = [f for f in d["consistency"] if f.startswith("[ERROR]")]
    assert errors == []


def test_render_briefing_contains_key_sections():
    d = dossier.assemble(seed=42, today=TODAY)
    text = dossier.render_briefing(d)
    assert "COVER DOSSIER" in text
    assert d["identity"]["name"] in text
    assert "TIMELINE" in text
    assert "RISK ASSESSMENT" in text
    assert "MEMORY ANCHORS" in text


def test_dossier_summary_shape():
    d = dossier.assemble(seed=42, today=TODAY)
    s = dossier.dossier_summary(d)
    assert s["name"] == d["identity"]["name"]
    assert s["documents"] == len(d["wallet"])
    assert s["contacts"] == len(d["network"])
    assert s["risk_band"] == d["risk"]["band"]
    assert s["consistency_issues"] == len(d["consistency"])


def test_different_seeds_differ():
    a = dossier.assemble(seed=1, today=TODAY)
    b = dossier.assemble(seed=2, today=TODAY)
    assert a["identity"]["name"] != b["identity"]["name"]
