"""Tests for cover_identity.documents -- fabricated paper trail."""

from __future__ import annotations

import datetime as dt
import random

from cover_identity import documents as docs
from cover_identity import generate

TODAY = dt.date(2024, 6, 1)


def _ident():
    return generate(seed=42)


def test_wallet_is_deterministic():
    ident = _ident()
    a = docs.build_wallet(ident, seed=5, today=TODAY)
    b = docs.build_wallet(ident, seed=5, today=TODAY)
    assert a == b


def test_wallet_has_expected_kinds():
    ident = _ident()
    wallet = docs.build_wallet(ident, seed=1, today=TODAY)
    kinds = {d["kind"] for d in wallet}
    assert {"library_card", "gym_membership", "utility_bill",
            "work_badge", "receipt"} <= kinds


def test_wallet_holder_names_match():
    ident = _ident()
    wallet = docs.build_wallet(ident, seed=2, today=TODAY)
    for doc in wallet:
        if "holder" in doc:
            assert doc["holder"] == ident["name"]


def test_documents_not_issued_before_adulthood():
    ident = _ident()
    wallet = docs.build_wallet(ident, seed=3, today=TODAY)
    dob = dt.date.fromisoformat(ident["date_of_birth"])
    for doc in wallet:
        if "issued" in doc:
            issued = dt.date.fromisoformat(doc["issued"])
            assert issued > dob


def test_receipts_sorted_by_date():
    ident = _ident()
    receipts = docs.make_receipts(ident, random.Random(4), count=5, today=TODAY)
    dates = [r["date"] for r in receipts]
    assert dates == sorted(dates)


def test_render_text_includes_fields():
    ident = _ident()
    card = docs.make_library_card(ident, random.Random(1), today=TODAY)
    text = docs.render_text(card)
    assert "LIBRARY CARD" in text
    assert ident["name"] in text


def test_wallet_report_counts():
    ident = _ident()
    wallet = docs.build_wallet(ident, seed=6, today=TODAY)
    report = docs.wallet_report(wallet)
    assert report["total"] == len(wallet)
    assert report["by_kind"]["receipt"] == 3
    assert report["earliest"] is not None
    assert report["latest"] is not None
    assert report["earliest"] <= report["latest"]


def test_utility_bill_uses_address():
    ident = _ident()
    bill = docs.make_utility_bill(ident, random.Random(2), today=TODAY)
    assert bill["address"] == ident["address"]
    assert bill["period"]
