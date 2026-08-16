"""Residence and safe-house layer for a cover identity.

A legend needs a place to be from. This module builds the residential
layer: the cover's stated home, a couple of safe houses with different
purposes, and the small neighborhood knowledge that makes the address
sound lived-in -- the name of the corner shop, which bus goes downtown,
what the neighbors complain about.

Neighborhood knowledge is the cheapest credibility there is. Anyone can
rent an address; only someone who lives there knows that the bakery
closes early on Thursdays. This module generates exactly that texture.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "ResidenceError",
    "Residence",
    "SafeHouse",
    "NeighborhoodKnowledge",
    "build_residence",
    "build_safe_houses",
    "build_neighborhood",
    "residence_brief",
]


class ResidenceError(ValueError):
    """Raised for residence-layer usage problems."""


@dataclass(frozen=True)
class Residence:
    """The cover's stated home."""

    address: str
    dwelling_type: str
    how_long: str
    landlord_story: str


_DWELLINGS = ["a rented flat above a shop", "a small terraced house",
              "a studio near the station", "a room in a shared house",
              "a converted loft by the canal"]
_HOW_LONG = ["about two years", "just over a year", "three years this spring",
             "since the last renovation", "a few months, still unpacking"]
_LANDLORD = ["an older couple who live abroad", "a letting agency downtown",
             "a retired teacher who checks in monthly", "a cousin of the previous tenant"]


def build_residence(rng: random.Random, address: str) -> Residence:
    """A deterministic residence record around a given street address."""
    if not address.strip():
        raise ResidenceError("address must not be empty")
    return Residence(
        address=address.strip(),
        dwelling_type=rng.choice(_DWELLINGS),
        how_long=rng.choice(_HOW_LONG),
        landlord_story=rng.choice(_LANDLORD),
    )


@dataclass(frozen=True)
class SafeHouse:
    """A fallback location with a stated purpose and readiness."""

    site_id: str
    purpose: str
    location_hint: str
    stocked: bool
    resupply_days: int


_PURPOSES = ["emergency overnight", "dead-drop servicing", "meeting neutral ground",
             "equipment cache", "observation post"]
_HINTS = ["the back room of the harbor warehouse", "the flat above the laundrette",
          "the locked garage on Mill Lane", "the cabin past the second lock",
          "the storage unit under the railway arch"]


def build_safe_houses(rng: random.Random, count: int = 2) -> List[SafeHouse]:
    """A deterministic set of safe houses with distinct purposes."""
    if count < 1:
        raise ResidenceError("count must be >= 1")
    count = min(count, len(_PURPOSES))
    houses: List[SafeHouse] = []
    for purpose, hint in rng.sample(list(zip(_PURPOSES, _HINTS)), count):
        houses.append(SafeHouse(
            site_id=f"safe-{len(houses) + 1}",
            purpose=purpose,
            location_hint=hint,
            stocked=rng.random() < 0.7,
            resupply_days=rng.randrange(7, 45),
        ))
    return houses


@dataclass
class NeighborhoodKnowledge:
    """The small facts that make an address sound lived-in."""

    corner_shop: str
    bus_route: str
    neighbor_complaint: str
    bakery_quirk: str
    pub_name: str

    def facts(self) -> List[str]:
        """All the facts as speakable sentences."""
        return [
            f"The corner shop is {self.corner_shop}.",
            f"The {self.bus_route} bus goes downtown.",
            f"The neighbors mostly complain about {self.neighbor_complaint}.",
            f"The bakery {self.bakery_quirk}.",
            f"The local pub is called {self.pub_name}.",
        ]


_SHOPS = ["Marsh's corner store", "the green grocer on the bend",
          "the all-night kiosk by the stop", "Petra's pantry"]
_COMPLAINTS = ["the parking", "the bins not being collected", "the noise from the yard",
               "the new bike lane"]
_BAKERY_QUIRKS = ["closes early on Thursdays", "does the good rye on Saturdays",
                  "runs out of rolls by ten", "is cash only"]
_PUBS = ["The Anchor", "The Broken Compass", "The Miller's Rest", "The Last Lamp"]


def build_neighborhood(rng: random.Random) -> NeighborhoodKnowledge:
    """A deterministic set of neighborhood facts."""
    return NeighborhoodKnowledge(
        corner_shop=rng.choice(_SHOPS),
        bus_route=f"the {rng.randrange(2, 90)}",
        neighbor_complaint=rng.choice(_COMPLAINTS),
        bakery_quirk=rng.choice(_BAKERY_QUIRKS),
        pub_name=rng.choice(_PUBS),
    )


def residence_brief(residence: Residence, safe_houses: List[SafeHouse],
                    neighborhood: NeighborhoodKnowledge) -> str:
    """Render the whole residential layer as a readable brief."""
    lines = [
        f"HOME: {residence.address}",
        f"  {residence.dwelling_type}, lived there {residence.how_long}",
        f"  landlord: {residence.landlord_story}",
        "",
        "NEIGHBORHOOD:",
    ]
    lines += [f"  - {fact}" for fact in neighborhood.facts()]
    lines.append("")
    lines.append("SAFE HOUSES:")
    for house in safe_houses:
        stocked = "stocked" if house.stocked else "NOT stocked"
        lines.append(f"  - {house.site_id}: {house.purpose} at "
                     f"{house.location_hint} ({stocked}, resupply every "
                     f"{house.resupply_days} days)")
    return "\n".join(lines)
