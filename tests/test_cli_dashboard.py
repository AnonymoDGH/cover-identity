"""Tests for the dashboard CLI command."""

from __future__ import annotations

from cover_identity.cli import main


def test_dashboard_basic(capsys):
    assert main(["dashboard", "--seeds", "1", "2", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "HANDLER DASHBOARD" in out
    assert "legend-1" in out
    assert "legend-2" in out


def test_dashboard_with_names(capsys):
    assert main(["dashboard", "--seeds", "1", "2", "--names", "berlin", "oslo",
                 "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "berlin" in out
    assert "oslo" in out


def test_dashboard_activate(capsys):
    assert main(["dashboard", "--seeds", "1", "--names", "berlin",
                 "--activate", "berlin", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "Active: berlin" in out


def test_dashboard_activate_unknown(capsys):
    rc = main(["dashboard", "--seeds", "1", "--names", "berlin",
               "--activate", "ghost", "--today", "2024-06-01"])
    assert rc == 2
    assert "error" in capsys.readouterr().err
