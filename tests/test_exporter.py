"""Tests for cover_identity.exporter -- multi-format dossier export."""

from __future__ import annotations

import datetime as dt
import json

import pytest

from cover_identity import dossier
from cover_identity import exporter as exp

TODAY = dt.date(2024, 6, 1)


def _dossier():
    return dossier.assemble(seed=42, today=TODAY)


def test_to_json_roundtrips():
    d = _dossier()
    text = exp.to_json(d)
    parsed = json.loads(text)
    assert parsed["identity"]["name"] == d["identity"]["name"]


def test_to_json_deterministic():
    d = _dossier()
    assert exp.to_json(d) == exp.to_json(d)


def test_to_json_missing_identity():
    with pytest.raises(exp.ExportError):
        exp.to_json({})


def test_to_markdown_contains_sections():
    d = _dossier()
    md = exp.to_markdown(d)
    assert md.startswith("# Cover Dossier")
    assert "## Basics" in md
    assert "## Backstory" in md
    assert "## Memory Anchors" in md
    assert "## Risk" in md
    assert d["identity"]["name"] in md


def test_to_cheat_sheet_minimal():
    d = _dossier()
    sheet = exp.to_cheat_sheet(d)
    assert "CHEAT SHEET" in sheet
    assert d["identity"]["name"] in sheet
    assert "ANCHORS:" in sheet
    assert "DURESS:" in sheet
    # The cheat sheet must NOT leak the full backstory.
    assert d["identity"]["backstory"] not in sheet


def test_to_redacted_strips_sensitive():
    d = _dossier()
    red = exp.to_redacted(d)
    assert red["identity"]["anchors"] == "[redacted]"
    assert red["identity"]["cover_questions"] == "[redacted]"
    assert red["identity"]["timeline"] == "[redacted]"
    # Basics survive.
    assert red["identity"]["name"] == d["identity"]["name"]
    assert red["note"]


def test_to_redacted_does_not_mutate_input():
    d = _dossier()
    before = d["identity"]["anchors"]
    exp.to_redacted(d)
    assert d["identity"]["anchors"] == before


def test_export_dispatch():
    d = _dossier()
    for fmt in exp.EXPORT_FORMATS:
        result = exp.export(d, fmt)
        assert isinstance(result, str)
        assert result


def test_export_unknown_format():
    d = _dossier()
    with pytest.raises(exp.ExportError):
        exp.export(d, "pdf")


def test_export_formats_tuple():
    assert set(exp.EXPORT_FORMATS) == {"json", "markdown", "cheat-sheet", "redacted"}
