"""Tests for cover_identity.metrics -- generator quality metrics."""

from __future__ import annotations

import datetime as dt

import pytest

from cover_identity import metrics

TODAY = dt.date(2024, 6, 1)


def test_sample_legends_count():
    legends = metrics.sample_legends(count=5, today=TODAY)
    assert len(legends) == 5


def test_sample_legends_min():
    with pytest.raises(ValueError):
        metrics.sample_legends(count=0)


def test_consistency_rate_perfect():
    legends = metrics.sample_legends(count=5, today=TODAY)
    # The generator should produce consistent legends.
    assert metrics.consistency_rate(legends) == 1.0


def test_consistency_rate_empty():
    assert metrics.consistency_rate([]) == 0.0


def test_risk_distribution_sums_to_sample():
    legends = metrics.sample_legends(count=6, today=TODAY)
    dist = metrics.risk_distribution(legends)
    assert sum(dist.values()) == 6


def test_diversity_report_high():
    legends = metrics.sample_legends(count=8, today=TODAY)
    report = metrics.diversity_report(legends)
    # Distinct seeds should give distinct names.
    assert report["name_diversity"] == 1.0
    assert report["occupation_diversity"] > 0.5


def test_diversity_report_single():
    legends = metrics.sample_legends(count=1, today=TODAY)
    report = metrics.diversity_report(legends)
    assert report["name_diversity"] == 1.0


def test_quality_report_shape():
    report = metrics.quality_report(count=5, today=TODAY)
    assert report["sample_size"] == 5
    assert 0.0 <= report["consistency_rate"] <= 1.0
    assert "diversity" in report
    assert sum(report["risk_distribution"].values()) == 5
