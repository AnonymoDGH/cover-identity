"""Tests for cover_identity.travel -- passport history."""

from __future__ import annotations

import datetime as dt
import random

from cover_identity import generate
from cover_identity import personas
from cover_identity import travel

TODAY = dt.date(2024, 6, 1)


def _ident(persona=None):
    ident = generate(seed=42)
    if persona:
        ident = personas.apply_persona(ident, persona, seed=1)
    return ident


def test_travel_volume_for_known_loudness():
    assert travel.travel_volume_for("low") == (1, 3)
    assert travel.travel_volume_for("large") == (5, 9)
    assert travel.travel_volume_for("unknown") == (2, 5)


def test_make_trip_after_adulthood():
    dob = dt.date(1990, 1, 1)
    trip = travel.make_trip(random.Random(1), dob, today=TODAY)
    start = dt.date.fromisoformat(trip["start"])
    assert start >= dob + dt.timedelta(days=365 * 18)
    assert start < TODAY
    assert trip["destination"] in travel.DESTINATIONS
    assert trip["purpose"] in travel.TRIP_PURPOSES


def test_build_travel_history_sorted():
    ident = _ident()
    trips = travel.build_travel_history(ident, seed=2, today=TODAY)
    starts = [t["start"] for t in trips]
    assert starts == sorted(starts)


def test_quiet_persona_travels_less():
    quiet = _ident("tradesperson")   # footprint_loudness "low" -> (1, 3)
    quiet_trips = travel.build_travel_history(quiet, seed=3, today=TODAY)
    assert 1 <= len(quiet_trips) <= 3


def test_loudness_directly_controls_volume():
    ident = _ident()
    # Force a loud footprint and confirm the volume band widens.
    ident["persona"] = {"footprint_loudness": "large"}
    trips = travel.build_travel_history(ident, seed=3, today=TODAY)
    assert 5 <= len(trips) <= 9


def test_travel_history_deterministic():
    ident = _ident()
    a = travel.build_travel_history(ident, seed=4, today=TODAY)
    b = travel.build_travel_history(ident, seed=4, today=TODAY)
    assert a == b


def test_travel_report_shape():
    ident = _ident()
    trips = travel.build_travel_history(ident, seed=5, today=TODAY)
    report = travel.travel_report(trips)
    assert report["trips"] == len(trips)
    assert report["destinations"] <= report["trips"]
    assert report["total_days"] > 0
    assert report["most_visited"] in travel.DESTINATIONS


def test_travel_report_empty():
    report = travel.travel_report([])
    assert report["trips"] == 0
    assert report["most_visited"] is None
