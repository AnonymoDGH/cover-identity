"""Tests for cover_identity.interrogation -- legend stress-testing."""

from __future__ import annotations

import datetime as dt

from cover_identity import dossier
from cover_identity import interrogation as iq

TODAY = dt.date(2024, 6, 1)


def _dossier():
    return dossier.assemble(seed=42, today=TODAY)


def test_build_probes_deterministic():
    d = _dossier()
    a = iq.build_probes(d["identity"], d["network"], d["wallet"], seed=1)
    b = iq.build_probes(d["identity"], d["network"], d["wallet"], seed=1)
    assert [p.question for p in a] == [p.question for p in b]


def test_probes_sorted_by_difficulty():
    d = _dossier()
    probes = iq.build_probes(d["identity"], d["network"], d["wallet"], seed=1)
    diffs = [p.difficulty for p in probes]
    assert diffs == sorted(diffs)


def test_probes_respect_max():
    d = _dossier()
    probes = iq.build_probes(d["identity"], d["network"], d["wallet"],
                             seed=1, max_probes=3)
    assert len(probes) <= 3


def test_probe_to_dict():
    p = iq.Probe("timeline", "Where were you in 2010?", 3, "hesitation")
    d = p.to_dict()
    assert d["facet"] == "timeline"
    assert d["difficulty"] == 3


def test_run_interrogation_confident_answers_hold():
    d = _dossier()
    def confident(q):
        return ("I grew up in the town I told you about, worked the jobs "
                "I listed, and I know my own history well enough.")
    report = iq.run_interrogation(d["identity"], confident,
                                  d["network"], d["wallet"], seed=1)
    assert report["verdict"] == "holds"
    assert report["overall"] >= 0.7


def test_run_interrogation_evasive_answers_crack():
    d = _dossier()
    def evasive(q):
        return "um, maybe, I guess, not sure."
    report = iq.run_interrogation(d["identity"], evasive,
                                  d["network"], d["wallet"], seed=1)
    assert report["verdict"] in {"strained", "cracks"}


def test_empty_reply_scores_zero():
    d = _dossier()
    report = iq.run_interrogation(d["identity"], lambda q: "",
                                  d["network"], d["wallet"], seed=1)
    assert report["overall"] == 0.0
    assert report["verdict"] == "cracks"


def test_interrogation_report_empty():
    report = iq.interrogation_report([])
    assert report["verdict"] == "no-probes"
    assert report["probes"] == 0


def test_report_has_by_facet():
    d = _dossier()
    report = iq.run_interrogation(d["identity"],
                                  lambda q: "a full and direct answer here",
                                  d["network"], d["wallet"], seed=1)
    assert report["by_facet"]
    for facet, score in report["by_facet"].items():
        assert 0.0 <= score <= 1.0
