"""Tests for cover_identity.readiness -- pre-deployment gates."""

from __future__ import annotations

import datetime as dt

from cover_identity import dossier
from cover_identity import readiness as rd

TODAY = dt.date(2024, 6, 1)


def _dossier():
    return dossier.assemble(seed=42, today=TODAY)


def test_full_dossier_is_go():
    d = _dossier()
    report = rd.readiness_report(d, drill_meter=100)
    assert report["verdict"] == "go"
    assert report["failed_count"] == 0


def test_low_drill_is_no_go():
    d = _dossier()
    report = rd.readiness_report(d, drill_meter=50)
    assert report["verdict"] == "no-go"
    assert "drill" in report["failed_names"]


def test_consistency_error_is_no_go():
    d = _dossier()
    d["consistency"] = ["[ERROR] age: stated 34 but DOB implies 32"]
    report = rd.readiness_report(d)
    assert report["verdict"] == "no-go"
    assert "consistency" in report["failed_names"]


def test_missing_documents_is_no_go():
    d = _dossier()
    d["wallet"] = [doc for doc in d["wallet"] if doc["kind"] != "work_badge"]
    report = rd.readiness_report(d)
    assert report["verdict"] == "no-go"
    assert "paper_trail" in report["failed_names"]


def test_empty_network_is_no_go():
    d = _dossier()
    d["network"] = []
    report = rd.readiness_report(d)
    assert report["verdict"] == "no-go"
    assert "network" in report["failed_names"]


def test_no_vouchers_is_no_go():
    d = _dossier()
    d["network"] = [{"name": "x", "closeness": 0.1}]
    report = rd.readiness_report(d)
    assert report["verdict"] == "no-go"


def test_high_risk_is_no_go():
    d = _dossier()
    d["risk"] = {"total": 0.9, "band": "burn-risk", "factors": {},
                 "worst_factor": "consistency"}
    report = rd.readiness_report(d)
    assert report["verdict"] == "no-go"
    assert "risk" in report["failed_names"]


def test_report_shape():
    d = _dossier()
    report = rd.readiness_report(d)
    assert len(report["gates"]) == 7
    for gate in report["gates"]:
        assert set(gate) == {"name", "passed", "reason"}


def test_verdict_helper():
    gates = [rd.Gate("a", True, "ok"), rd.Gate("b", True, "ok")]
    assert rd.verdict(gates) == "go"
    gates.append(rd.Gate("c", False, "bad"))
    assert rd.verdict(gates) == "no-go"
