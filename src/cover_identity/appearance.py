"""Physical description and disguise kit for a cover identity.

Witnesses remember clothes before faces. This module builds the appearance
layer of a legend: a baseline physical description consistent with the
identity, a rotating wardrobe of forgettable outfits, and a disguise kit
with reversible changes -- the kind that alter a silhouette without
requiring acting skill.

The key idea is *reversibility*: every disguise item can be added or
removed in under a minute in a restroom, and the module tracks which
combination is currently "on" so the operator never forgets what they
look like right now versus what their documents say.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "AppearanceError",
    "Description",
    "DisguiseItem",
    "Wardrobe",
    "DisguiseKit",
    "build_description",
]


class AppearanceError(ValueError):
    """Raised for appearance/disguise usage problems."""


@dataclass(frozen=True)
class Description:
    """Baseline physical description matching the identity's age."""

    height_cm: int
    build: str
    hair: str
    distinguishing: str

    def to_text(self) -> str:
        return (f"{self.height_cm} cm, {self.build} build, {self.hair} hair; "
                f"{self.distinguishing}")


_BUILDS = ["slight", "medium", "stocky", "broad-shouldered"]
_HAIR = ["dark", "light", "grey-streaked", "reddish", "salt-and-pepper"]
_DISTINGUISHING = [
    "a small scar over the left eyebrow",
    "wears plain glasses for reading",
    "a faded watch tan on the left wrist",
    "walks with a slight limp after an old injury",
    "no distinguishing marks",
]


def build_description(rng: random.Random, age: int) -> Description:
    """A deterministic baseline description scaled to the cover's age."""
    if age < 0:
        raise AppearanceError("age must be >= 0")
    height = rng.randrange(158, 196)
    build = rng.choice(_BUILDS)
    hair = rng.choice(_HAIR) if age < 45 else rng.choice(
        ["grey", "grey-streaked", "salt-and-pepper", "thinning"])
    return Description(height_cm=height, build=build, hair=hair,
                       distinguishing=rng.choice(_DISTINGUISHING))


@dataclass(frozen=True)
class DisguiseItem:
    """One reversible appearance change."""

    name: str
    slot: str          # head, face, torso, hands, gait
    seconds: int       # time to add or remove
    effect: str

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise AppearanceError("seconds must be positive")


#: The standard catalog of reversible items.
CATALOG: List[DisguiseItem] = [
    DisguiseItem("knit cap", "head", 5, "changes the head silhouette"),
    DisguiseItem("baseball cap", "head", 5, "shades the eyes and hairline"),
    DisguiseItem("clear-lens glasses", "face", 3, "alters the eye area"),
    DisguiseItem("false stubble patch", "face", 40, "adds jaw texture"),
    DisguiseItem("loose work jacket", "torso", 10, "hides the body line"),
    DisguiseItem("high-visibility vest", "torso", 8, "makes the wearer look like staff"),
    DisguiseItem("fingerless gloves", "hands", 6, "hides ring marks and knuckles"),
    DisguiseItem("pebble in the shoe", "gait", 20, "changes the walk temporarily"),
]


class Wardrobe:
    """A rotation of forgettable outfits, one per day-slot."""

    def __init__(self, rng: random.Random, days: int = 7) -> None:
        if days < 1:
            raise AppearanceError("days must be >= 1")
        palettes = [
            "grey jacket, dark trousers, plain shoes",
            "navy sweater, work trousers, boots",
            "olive shirt, canvas trousers, trainers",
            "brown coat, corduroy trousers, loafers",
            "black fleece, grey trousers, walking shoes",
        ]
        self._outfits: List[str] = [rng.choice(palettes) for _ in range(days)]

    def outfit_for_day(self, day: int) -> str:
        """The outfit for a 0-based day index, wrapping weekly."""
        return self._outfits[day % len(self._outfits)]

    def __len__(self) -> int:
        return len(self._outfits)


class DisguiseKit:
    """Tracks which reversible items are currently applied."""

    def __init__(self, items: Optional[List[DisguiseItem]] = None) -> None:
        self._catalog = {item.name: item for item in (items or CATALOG)}
        self._applied: Dict[str, DisguiseItem] = {}

    def available(self) -> List[str]:
        return sorted(self._catalog)

    def apply(self, name: str) -> DisguiseItem:
        """Add an item. One item per slot; applying a second to the same
        slot replaces the first."""
        if name not in self._catalog:
            raise AppearanceError(f"unknown item {name!r}")
        item = self._catalog[name]
        # Remove any other item in the same slot.
        for existing in list(self._applied.values()):
            if existing.slot == item.slot and existing.name != item.name:
                del self._applied[existing.name]
        self._applied[name] = item
        return item

    def remove(self, name: str) -> DisguiseItem:
        if name not in self._applied:
            raise AppearanceError(f"item {name!r} is not applied")
        return self._applied.pop(name)

    def applied(self) -> List[DisguiseItem]:
        return sorted(self._applied.values(), key=lambda i: i.name)

    def change_seconds(self) -> int:
        """Total seconds to fully reverse the current disguise."""
        return sum(item.seconds for item in self._applied.values())

    def slots_covered(self) -> List[str]:
        return sorted({item.slot for item in self._applied.values()})
