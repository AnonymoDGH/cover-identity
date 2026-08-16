"""Vehicle and route layer for a cover identity.

A cover that claims to drive but cannot describe its own car is a small
crack that widens under pressure. This module builds the vehicle layer:
one primary vehicle with a plausible plate and history, an honest set of
routes the operator should know cold, and a fueling/maintenance pattern
that matches the budget.

Routes are described as sequences of waypoints with a purpose, so the
operator can be drilled on them ("how do you get to the harbor from your
flat?") and the answers stay consistent.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "VehicleError",
    "Vehicle",
    "Route",
    "build_vehicle",
    "build_routes",
    "vehicle_card",
]


class VehicleError(ValueError):
    """Raised for vehicle-layer usage problems."""


_MAKES = ["an older estate car", "a small hatchback", "a plain sedan",
          "a light van with company markings", "a secondhand pickup"]
_COLORS = ["grey", "navy", "dark green", "white", "burgundy"]
_HISTORIES = [
    "bought secondhand from a dealer across town",
    "inherited from a relative, kept for reliability",
    "bought at auction, runs well enough",
    "a long-term lease through the employer",
]


@dataclass(frozen=True)
class Vehicle:
    """The cover's primary vehicle."""

    plate: str
    make: str
    color: str
    history: str
    fuel: str


def _plate(rng: random.Random) -> str:
    """A neutral, fictional plate: two letters, three digits, two letters."""
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    return ("".join(rng.choice(letters) for _ in range(2)) + "-" +
            f"{rng.randrange(100, 999)}-" +
            "".join(rng.choice(letters) for _ in range(2)))


def build_vehicle(rng: random.Random) -> Vehicle:
    """A deterministic vehicle record."""
    return Vehicle(
        plate=_plate(rng),
        make=rng.choice(_MAKES),
        color=rng.choice(_COLORS),
        history=rng.choice(_HISTORIES),
        fuel=rng.choice(["petrol", "diesel"]),
    )


@dataclass(frozen=True)
class Route:
    """A route the operator must know cold."""

    name: str
    purpose: str
    waypoints: List[str]

    def describe(self) -> str:
        return f"{self.name} ({self.purpose}): " + " -> ".join(self.waypoints)


_ROUTE_TEMPLATES: List[Dict] = [
    {"name": "home to work", "purpose": "the daily commute",
     "waypoints": ["the flat", "the canal bridge", "the market square", "the workplace"]},
    {"name": "home to harbor", "purpose": "the weekend errand",
     "waypoints": ["the flat", "the hill road", "the fish market", "the harbor"]},
    {"name": "home to station", "purpose": "picking up visitors",
     "waypoints": ["the flat", "the ring road", "the station forecourt"]},
    {"name": "fallback exit", "purpose": "leaving town fast, no main roads",
     "waypoints": ["the flat", "the back lanes", "the old toll bridge", "the coast road"]},
]


def build_routes(rng: random.Random, count: int = 3) -> List[Route]:
    """A deterministic set of routes, distinct by name."""
    if count < 1:
        raise VehicleError("count must be >= 1")
    count = min(count, len(_ROUTE_TEMPLATES))
    routes: List[Route] = []
    for template in rng.sample(_ROUTE_TEMPLATES, count):
        routes.append(Route(
            name=template["name"],
            purpose=template["purpose"],
            waypoints=list(template["waypoints"]),
        ))
    return routes


def vehicle_card(vehicle: Vehicle, name: str) -> str:
    """Render the vehicle as a glovebox-card style text block."""
    return "\n".join([
        "VEHICLE CARD",
        f"  keeper:  {name}",
        f"  plate:   {vehicle.plate}",
        f"  car:     {vehicle.color} {vehicle.make}",
        f"  fuel:    {vehicle.fuel}",
        f"  origin:  {vehicle.history}",
    ])
