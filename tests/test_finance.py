"""Tests for cover_identity.finance -- cover financial history."""

from __future__ import annotations

import datetime as dt
import random

import pytest

from cover_identity import corpus
from cover_identity import finance
from cover_identity import generate

TODAY = dt.date(2024, 6, 1)


def _ident():
    return generate(seed=42)


def test_income_for_known_occupation_in_range():
    for sector, jobs in corpus.OCCUPATIONS.items():
        lo, hi = finance._INCOME_RANGES[sector]
        income = finance.income_for_occupation(jobs[0], random.Random(1))
        assert lo <= income <= hi


def test_income_unknown_occupation_defaults():
    income = finance.income_for_occupation("mystery job", random.Random(1))
    lo, hi = finance._INCOME_RANGES["logistics"]
    assert lo <= income <= hi


def test_build_budget_sums_below_income():
    income = 3000
    budget = finance.build_budget(income, random.Random(2))
    assert set(budget) == set(finance.BUDGET_CATEGORIES)
    assert sum(budget.values()) <= income
    assert budget["savings"] > 0
    assert budget["rent"] > budget["phone"]


def test_build_budget_rejects_nonpositive():
    with pytest.raises(ValueError):
        finance.build_budget(0, random.Random(1))


def test_build_budget_deterministic():
    a = finance.build_budget(3000, random.Random(3))
    b = finance.build_budget(3000, random.Random(3))
    assert a == b


def test_transactions_sorted_and_shaped():
    txs = finance.build_transactions(random.Random(4), count=10, today=TODAY)
    dates = [t["date"] for t in txs]
    assert dates == sorted(dates)
    for t in txs:
        assert t["category"] in finance.build_transactions.__defaults__ or t["category"]
        assert "." in t["amount"]


def test_credit_profile_average_and_age_scaled():
    profile = finance.credit_profile(random.Random(5), age=40)
    assert 620 <= profile["score"] <= 740
    assert profile["rating"] == "average"
    assert 1 <= profile["history_years"] <= 22

    young = finance.credit_profile(random.Random(5), age=19)
    assert young["history_years"] <= 1


def test_build_financial_history_shape():
    ident = _ident()
    history = finance.build_financial_history(ident, seed=6, today=TODAY)
    assert history["income_source"] == ident["employer"]
    assert history["monthly_income"] > 0
    assert history["budget"]
    assert history["transactions"]
    assert history["credit"]["score"]


def test_finance_report_balanced():
    ident = _ident()
    history = finance.build_financial_history(ident, seed=7, today=TODAY)
    report = finance.finance_report(history)
    assert report["balanced"] is True
    assert report["surplus"] >= 0
    assert report["credit_score"] == history["credit"]["score"]


def test_financial_history_deterministic():
    ident = _ident()
    a = finance.build_financial_history(ident, seed=8, today=TODAY)
    b = finance.build_financial_history(ident, seed=8, today=TODAY)
    assert a == b
