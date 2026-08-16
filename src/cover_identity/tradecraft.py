"""Tradecraft primitives for operating a cover identity.

A legend is a document; tradecraft is what you do with it in the field.
This module models the small operational building blocks around a cover:
dead drops, brush passes, surveillance-detection routes, and signal
sites. Everything is abstract and fictional -- coordinates are grid
references on a notional map, not real places -- but the logic is real:
timing windows, contingency rules, and route validation.

The point is to give a roleplay or testing scenario a coherent,
deterministic operational layer that hangs together with the legend.
"""

from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "TradecraftError",
    "DeadDrop",
    "BrushPass",
    "SDRLeg",
    "SDRRoute",
    "SignalSite",
    "make_dead_drop",
    "make_brush_pass",
    "build_sdr",
    "validate_sdr",
    "make_signal_site",
    "operations_plan",
]


class TradecraftError(ValueError):
    """Raised for invalid operational parameters."""


# ---------------------------------------------------------------------------
# Dead drops
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeadDrop:
    """A hidden location where material can be left without meeting."""

    site_id: str
    grid: Tuple[int, int]
    container: str
    loading_window: str   # e.g. "02:00-04:00"
    signal: str           # how the loader marks it as loaded
    contingency: str      # what to do if the site is blown


_CONTAINERS = ["magnetic box", "hollow bolt", "fake drainpipe",
               "loose brick cavity", "sealed tube under bench"]
_SIGNALS = ["chalk mark on the lamppost", "tape on the mailbox",
            "pebble moved to the left of the gate", "knot tied in the fence wire"]
_CONTINGENCIES = ["switch to backup site", "abort and re-signal in 48h",
                  "leave material, walk away, report"]


def make_dead_drop(rng: random.Random, site_id: str,
                   grid_size: int = 100) -> DeadDrop:
    """Create a deterministic dead drop on a notional grid map."""
    if not site_id.strip():
        raise TradecraftError("site_id must not be empty")
    if grid_size < 10:
        raise TradecraftError("grid_size must be >= 10")
    hour = rng.randrange(0, 5) * 2  # even hours in the small window
    window = f"{hour:02d}:00-{hour + 2:02d}:00"
    return DeadDrop(
        site_id=site_id.strip(),
        grid=(rng.randrange(grid_size), rng.randrange(grid_size)),
        container=rng.choice(_CONTAINERS),
        loading_window=window,
        signal=rng.choice(_SIGNALS),
        contingency=rng.choice(_CONTINGENCIES),
    )


# ---------------------------------------------------------------------------
# Brush passes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrushPass:
    """A brief, deniable hand-off between two people in motion."""

    location: str
    time: str
    exchange_cue: str     # the phrase or gesture that triggers the pass
    fallback: str


_LOCATIONS = ["the market arcade", "the station footbridge",
              "the museum cloakroom", "the harbor fish stall",
              "the library return desk"]
_CUES = ["asking for the time", "dropping a glove and returning it",
         "exchanging a folded newspaper", "a nod at the clock"]


def make_brush_pass(rng: random.Random) -> BrushPass:
    """Create a deterministic brush pass plan."""
    hour = rng.randrange(8, 20)
    minute = rng.choice([0, 15, 30, 45])
    return BrushPass(
        location=rng.choice(_LOCATIONS),
        time=f"{hour:02d}:{minute:02d}",
        exchange_cue=rng.choice(_CUES),
        fallback="if either party is late by 5 minutes, abort and retry tomorrow",
    )


# ---------------------------------------------------------------------------
# Surveillance detection routes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SDRLeg:
    """One leg of a surveillance-detection route."""

    waypoint: str
    purpose: str          # what this leg is designed to reveal
    dwell_minutes: int


@dataclass
class SDRRoute:
    """A full surveillance-detection route: ordered legs with a goal."""

    legs: List[SDRLeg] = field(default_factory=list)
    goal: str = "confirm clean before a sensitive meeting"

    @property
    def total_minutes(self) -> int:
        return sum(leg.dwell_minutes for leg in self.legs)


_LEG_PURPOSES = [
    ("enter a shop with one exit", "force a follower to commit or peel off"),
    ("cross an open square", "expose anyone keeping a fixed distance"),
    ("ride two stops and back", "reveal a static tail on the same line"),
    ("stop at a cafe facing the entrance", "observe who lingers without entering"),
    ("take a staircase that loops", "bring a follower into open view"),
]


def build_sdr(rng: random.Random, legs: int = 4) -> SDRRoute:
    """Build a deterministic SDR with the requested number of legs.

    Each leg uses a distinct purpose so the route actually tests for
    surveillance rather than repeating the same trick.
    """
    if legs < 2:
        raise TradecraftError("an SDR needs at least 2 legs")
    if legs > len(_LEG_PURPOSES):
        legs = len(_LEG_PURPOSES)
    route = SDRRoute()
    for waypoint, purpose in rng.sample(_LEG_PURPOSES, legs):
        route.legs.append(SDRLeg(
            waypoint=waypoint,
            purpose=purpose,
            dwell_minutes=rng.randrange(5, 21),
        ))
    return route


def validate_sdr(route: SDRRoute) -> List[str]:
    """Check an SDR for common design flaws. Returns a list of problems."""
    problems: List[str] = []
    if len(route.legs) < 2:
        problems.append("route has fewer than 2 legs")
    purposes = [leg.purpose for leg in route.legs]
    if len(purposes) != len(set(purposes)):
        problems.append("route repeats a detection technique")
    if route.total_minutes < 20:
        problems.append("route is too short to shake a determined tail")
    if any(leg.dwell_minutes <= 0 for leg in route.legs):
        problems.append("a leg has a non-positive dwell time")
    return problems


# ---------------------------------------------------------------------------
# Signal sites
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalSite:
    """A site where a pre-arranged mark conveys a one-bit message."""

    site_id: str
    mark: str
    meaning: str
    wipe_after: bool


def make_signal_site(rng: random.Random, site_id: str, meaning: str) -> SignalSite:
    """Create a deterministic signal site for a one-bit message."""
    if not meaning.strip():
        raise TradecraftError("meaning must not be empty")
    return SignalSite(
        site_id=site_id.strip(),
        mark=rng.choice(_SIGNALS),
        meaning=meaning.strip(),
        wipe_after=rng.random() < 0.5,
    )


# ---------------------------------------------------------------------------
# Operations plan
# ---------------------------------------------------------------------------

def operations_plan(seed: Optional[int] = None,
                    today: Optional[dt.date] = None) -> Dict:
    """Assemble a deterministic, fictional operations plan.

    Bundles a dead drop, a brush pass, an SDR, and two signal sites into
    one dict, dated relative to the reference date.
    """
    rng = random.Random(seed)
    today = today or dt.date.today()
    return {
        "prepared": today.isoformat(),
        "dead_drop": make_dead_drop(rng, "primary"),
        "backup_drop": make_dead_drop(rng, "backup"),
        "brush_pass": make_brush_pass(rng),
        "sdr": build_sdr(rng, legs=4),
        "signals": [
            make_signal_site(rng, "go", "proceed as planned"),
            make_signal_site(rng, "no-go", "abort; danger"),
        ],
    }
