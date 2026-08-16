"""Tests for cover_identity.risk -- exposure-risk assessment."""

from __future__ import annotations

import datetime as dt

from cover_identity import documents as docs
from cover_identity import network as net
from cover_identity import digital_footprint as fp
from cover_identity import generate
from cover_identity import risk

TODAY = dt.date(2024, 6, 1)


def _full():
    ident = generate(seed=42)
    footprint = fp.build_footprint(ident, seed=1, today=TODAY)
    network = net.build_network(seed=1, size=5)
    wallet = docs.build_wallet(ident, seed=1, today=TODAY)
    return ident, footprint, network, wallet


def test_assess_returns_all_factors():
    ident, footprint, network, wallet = _full()
    report = risk.assess(ident, footprint, network, wallet)
    assert set(report["factors"]) == set(risk.RISK_WEIGHTS)
    assert 0.0 <= report["total"] <= 1.0
    assert report["band"] in {"solid", "workable", "shaky", "burn-risk"}
    assert report["worst_factor"] in report["factors"]


def test_weights_sum_to_one():
    assert abs(sum(risk.RISK_WEIGHTS.values()) - 1.0) < 1e-9


def test_clean_identity_scores_low_consistency_risk():
    ident = generate(seed=42)
    assert risk.score_consistency(ident) == 0.0


def test_broken_identity_scores_high_consistency_risk():
    ident = generate(seed=42)
    ident["age"] = ident["age"] + 10
    assert risk.score_consistency(ident) > 0.3


def test_no_footprint_is_riskier_than_sparse():
    ident = generate(seed=42)
    footprint = fp.build_footprint(ident, seed=1, today=TODAY)
    assert risk.score_footprint(None) > risk.score_footprint(footprint)


def test_loud_footprint_is_riskiest():
    loud = {"profiles": [{"followers": 900}]}
    assert risk.score_footprint(loud) >= 0.9


def test_network_with_vouchers_is_safer():
    strong = net.build_network(seed=2, size=6)
    assert risk.score_network(strong) < risk.score_network(None)


def test_paper_trail_missing_documents_costs():
    ident = generate(seed=42)
    full = docs.build_wallet(ident, seed=1, today=TODAY)
    assert risk.score_paper_trail(full) < risk.score_paper_trail(None)


def test_risk_band_thresholds():
    assert risk.risk_band(0.1) == "solid"
    assert risk.risk_band(0.4) == "workable"
    assert risk.risk_band(0.6) == "shaky"
    assert risk.risk_band(0.9) == "burn-risk"


def test_full_legend_is_workable_or_better():
    ident, footprint, network, wallet = _full()
    report = risk.assess(ident, footprint, network, wallet)
    assert report["band"] in {"solid", "workable"}
