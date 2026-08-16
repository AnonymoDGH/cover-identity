"""Tests for cover_identity.vehicles -- vehicle and route layer."""

from __future__ import annotations

import random

import pytest

from cover_identity import vehicles as veh


def test_build_vehicle_deterministic():
    a = veh.build_vehicle(random.Random(1))
    b = veh.build_vehicle(random.Random(1))
    assert a == b


def test_plate_format():
    v = veh.build_vehicle(random.Random(2))
    parts = v.plate.split("-")
    assert len(parts) == 3
    assert len(parts[0]) == 2 and parts[0].isalpha()
    assert parts[1].isdigit() and len(parts[1]) == 3
    assert len(parts[2]) == 2 and parts[2].isalpha()


def test_vehicle_fields():
    v = veh.build_vehicle(random.Random(3))
    assert v.make in veh._MAKES
    assert v.color in veh._COLORS
    assert v.fuel in {"petrol", "diesel"}


def test_build_routes_distinct():
    routes = veh.build_routes(random.Random(4), count=3)
    names = [r.name for r in routes]
    assert len(names) == len(set(names)) == 3


def test_build_routes_clamped():
    routes = veh.build_routes(random.Random(5), count=99)
    assert len(routes) == len(veh._ROUTE_TEMPLATES)


def test_build_routes_min():
    with pytest.raises(veh.VehicleError):
        veh.build_routes(random.Random(1), count=0)


def test_route_describe():
    routes = veh.build_routes(random.Random(6), count=1)
    text = routes[0].describe()
    assert "->" in text
    assert routes[0].name in text


def test_vehicle_card():
    v = veh.build_vehicle(random.Random(7))
    card = veh.vehicle_card(v, "Ada Lovelace")
    assert "VEHICLE CARD" in card
    assert "Ada Lovelace" in card
    assert v.plate in card
