"""Tests for the checklist/metrics/debrief/readiness/scenarios CLI commands."""

from __future__ import annotations

import io

import pytest

from cover_identity.cli import main


def test_checklist_list(capsys):
    assert main(["checklist", "--list"]) == 0
    out = capsys.readouterr().out
    assert "pre-meeting" in out
    assert "pre-travel" in out
    assert "post-incident" in out


def test_checklist_default(capsys):
    assert main(["checklist"]) == 0
    out = capsys.readouterr().out
    assert "CHECKLIST: pre-meeting" in out


def test_checklist_named(capsys):
    assert main(["checklist", "pre-travel"]) == 0
    out = capsys.readouterr().out
    assert "CHECKLIST: pre-travel" in out


def test_checklist_unknown(capsys):
    rc = main(["checklist", "nonexistent"])
    assert rc == 2
    assert "error" in capsys.readouterr().err


def test_metrics(capsys):
    assert main(["metrics", "--count", "5", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "Sample size:        5" in out
    assert "Consistency rate:" in out
    assert "Diversity:" in out


def test_debrief_from_stdin(capsys, monkeypatch):
    stdin = io.StringIO(
        "Where do you live? | address | clean\n"
        "What year were you born? | timeline | invented\n"
    )
    monkeypatch.setattr("sys.stdin", stdin)
    assert main(["debrief", "berlin"]) == 0
    out = capsys.readouterr().out
    assert "Legend: berlin" in out
    assert "timeline" in out
    assert "Recommendation:" in out


def test_debrief_bad_line(capsys, monkeypatch):
    stdin = io.StringIO("not a valid line\n")
    monkeypatch.setattr("sys.stdin", stdin)
    rc = main(["debrief", "berlin"])
    assert rc == 2
    assert "error" in capsys.readouterr().err


def test_debrief_bad_outcome(capsys, monkeypatch):
    stdin = io.StringIO("q | f | spectacular\n")
    monkeypatch.setattr("sys.stdin", stdin)
    rc = main(["debrief", "berlin"])
    assert rc == 2


def test_readiness_go(capsys):
    rc = main(["readiness", "--seed", "42", "--today", "2024-06-01",
               "--drill-meter", "100"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "GO" in out


def test_readiness_no_go(capsys):
    rc = main(["readiness", "--seed", "42", "--today", "2024-06-01",
               "--drill-meter", "20"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "NO-GO" in out


def test_scenarios(capsys):
    assert main(["scenarios", "--seed", "42", "--count", "3"]) == 0
    out = capsys.readouterr().out
    assert out.count("SCENARIO:") == 3
