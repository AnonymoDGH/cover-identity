"""Tests for cover_identity.handler -- multi-legend dashboard."""

from __future__ import annotations

import datetime as dt

import pytest

from cover_identity import dossier as dossier_mod
from cover_identity import handler as hd

TODAY = dt.date(2024, 6, 1)


def _dashboard():
    dash = hd.HandlerDashboard()
    dash.add_legend("berlin", dossier_mod.assemble(seed=1, today=TODAY))
    dash.add_legend("oslo", dossier_mod.assemble(seed=2, today=TODAY))
    return dash


def test_add_and_overview():
    dash = _dashboard()
    overview = dash.overview(TODAY)
    assert overview["total"] == 2
    names = {row["name"] for row in overview["legends"]}
    assert names == {"berlin", "oslo"}


def test_add_duplicate_rejected():
    dash = _dashboard()
    with pytest.raises(hd.HandlerError):
        dash.add_legend("berlin", dossier_mod.assemble(seed=3, today=TODAY))


def test_activate_unknown_rejected():
    dash = _dashboard()
    with pytest.raises(hd.HandlerError):
        dash.activate("ghost", TODAY)


def test_activate_and_active():
    dash = _dashboard()
    dash.activate("berlin", TODAY)
    overview = dash.overview(TODAY)
    assert overview["active"] == "berlin"


def test_retire_and_burn():
    dash = _dashboard()
    dash.activate("berlin", TODAY)
    dash.retire("berlin")
    assert dash.overview(TODAY)["active"] is None
    dash.burn("oslo")
    statuses = {r["name"]: r["status"] for r in dash.overview(TODAY)["legends"]}
    assert statuses["oslo"] == "burned"


def test_readiness_per_legend():
    dash = _dashboard()
    report = dash.readiness("berlin", drill_meter=100)
    assert report["verdict"] in {"go", "no-go"}


def test_readiness_unknown_rejected():
    dash = _dashboard()
    with pytest.raises(hd.HandlerError):
        dash.readiness("ghost")


def test_due_for_rotation():
    dash = _dashboard()
    dash.activate("berlin", TODAY, horizon_days=5)
    assert dash.overview(TODAY)["due_for_rotation"] == []
    later = TODAY + dt.timedelta(days=6)
    assert dash.overview(later)["due_for_rotation"] == ["berlin"]


def test_dashboard_to_text():
    dash = _dashboard()
    dash.activate("berlin", TODAY)
    text = hd.dashboard_to_text(dash, TODAY)
    assert "HANDLER DASHBOARD" in text
    assert "berlin" in text
    assert "oslo" in text
    assert "Active: berlin" in text


def test_dashboard_to_text_no_active():
    dash = _dashboard()
    text = hd.dashboard_to_text(dash, TODAY)
    assert "Active: (none)" in text
