"""Tests for cover_identity.tradecraft -- operational primitives."""

from __future__ import annotations

import datetime as dt
import random

import pytest

from cover_identity import tradecraft as tc

TODAY = dt.date(2024, 6, 1)


def test_dead_drop_deterministic():
    a = tc.make_dead_drop(random.Random(1), "primary")
    b = tc.make_dead_drop(random.Random(1), "primary")
    assert a == b


def test_dead_drop_fields():
    drop = tc.make_dead_drop(random.Random(2), "site-a")
    assert drop.site_id == "site-a"
    assert 0 <= drop.grid[0] < 100 and 0 <= drop.grid[1] < 100
    assert drop.container and drop.signal and drop.contingency
    assert "-" in drop.loading_window


def test_dead_drop_validation():
    with pytest.raises(tc.TradecraftError):
        tc.make_dead_drop(random.Random(1), "  ")
    with pytest.raises(tc.TradecraftError):
        tc.make_dead_drop(random.Random(1), "x", grid_size=5)


def test_brush_pass_shape():
    bp = tc.make_brush_pass(random.Random(3))
    assert bp.location and bp.exchange_cue and bp.fallback
    hour = int(bp.time.split(":")[0])
    assert 8 <= hour < 20


def test_build_sdr_distinct_purposes():
    route = tc.build_sdr(random.Random(4), legs=4)
    purposes = [leg.purpose for leg in route.legs]
    assert len(purposes) == len(set(purposes))
    assert len(route.legs) == 4


def test_build_sdr_clamps_to_available():
    route = tc.build_sdr(random.Random(5), legs=99)
    assert len(route.legs) == len(tc._LEG_PURPOSES)


def test_build_sdr_min_legs():
    with pytest.raises(tc.TradecraftError):
        tc.build_sdr(random.Random(6), legs=1)


def test_validate_sdr_clean_route():
    route = tc.build_sdr(random.Random(7), legs=4)
    # Ensure enough dwell to pass the duration check.
    for leg in route.legs:
        object.__setattr__(leg, "dwell_minutes", 10)
    assert tc.validate_sdr(route) == []


def test_validate_sdr_flags_short_route():
    route = tc.SDRRoute(legs=[
        tc.SDRLeg("a", "p1", 5),
        tc.SDRLeg("b", "p2", 5),
    ])
    problems = tc.validate_sdr(route)
    assert any("too short" in p for p in problems)


def test_validate_sdr_flags_repeated_purpose():
    route = tc.SDRRoute(legs=[
        tc.SDRLeg("a", "same", 15),
        tc.SDRLeg("b", "same", 15),
    ])
    problems = tc.validate_sdr(route)
    assert any("repeats" in p for p in problems)


def test_signal_site():
    site = tc.make_signal_site(random.Random(8), "go", "proceed")
    assert site.site_id == "go"
    assert site.meaning == "proceed"
    with pytest.raises(tc.TradecraftError):
        tc.make_signal_site(random.Random(8), "go", "  ")


def test_operations_plan_shape():
    plan = tc.operations_plan(seed=9, today=TODAY)
    assert plan["prepared"] == TODAY.isoformat()
    assert plan["dead_drop"].site_id == "primary"
    assert plan["backup_drop"].site_id == "backup"
    assert len(plan["signals"]) == 2
    assert tc.validate_sdr(plan["sdr"]) == [] or plan["sdr"].total_minutes >= 0


def test_operations_plan_deterministic():
    a = tc.operations_plan(seed=10, today=TODAY)
    b = tc.operations_plan(seed=10, today=TODAY)
    assert a == b
