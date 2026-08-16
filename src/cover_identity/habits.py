"""Daily-routine and habit layer for a cover identity.

Routine is the skeleton of a legend. When someone asks "what did you do
yesterday?" the answer must come out without thought, and it must be the
same answer next week. This module builds a deterministic daily routine
anchored to the cover's occupation and hobbies, plus a handful of small
habits -- the coffee order, the paper they read, the walk they take --
that make the person feel lived-in.

The routine is expressed as time-of-day blocks so it can be drilled
("where are you at 3 p.m. on a Tuesday?") and so it can be checked
against the comms schedule and the alibi builder for contradictions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "HabitsError",
    "RoutineBlock",
    "Habits",
    "build_routine",
    "build_habits",
    "routine_to_text",
    "where_at",
]


class HabitsError(ValueError):
    """Raised for routine/habit usage problems."""


@dataclass(frozen=True)
class RoutineBlock:
    """One block of the daily routine."""

    start_hour: int
    end_hour: int
    activity: str
    location: str

    def covers(self, hour: int) -> bool:
        return self.start_hour <= hour < self.end_hour


def build_routine(rng: random.Random, occupation: str) -> List[RoutineBlock]:
    """A deterministic weekday routine scaled to the occupation.

    Blocks are contiguous from early morning to evening with no gaps, so
    any hour of the day maps to exactly one activity.
    """
    blocks: List[RoutineBlock] = []
    blocks.append(RoutineBlock(6, 8, "waking up, breakfast, getting ready", "the flat"))
    blocks.append(RoutineBlock(8, 9, "the commute", "in transit"))
    blocks.append(RoutineBlock(9, 12, f"morning {occupation} work", "the workplace"))
    blocks.append(RoutineBlock(12, 13, "lunch", rng.choice(["the cafe", "the canteen", "a bench nearby"])))
    blocks.append(RoutineBlock(13, 17, f"afternoon {occupation} work", "the workplace"))
    blocks.append(RoutineBlock(17, 18, "the commute home", "in transit"))
    hobby = rng.choice(corpus.HOBBIES)
    blocks.append(RoutineBlock(18, 20, f"unwinding with {hobby}", "the flat"))
    blocks.append(RoutineBlock(20, 22, "dinner and reading", "the flat"))
    return blocks


_COFFEES = ["a black coffee, no sugar", "a flat white", "tea with a little milk",
            "an espresso, double"]
_PAPERS = ["the local broadsheet", "a trade magazine", "the crossword paper",
           "nothing, just listens to the radio"]
_WALKS = ["along the canal", "through the market square", "up the hill road",
          "around the harbor"]


@dataclass
class Habits:
    """The small, repeatable details that make a person feel real."""

    coffee_order: str
    reads: str
    walk: str
    weekday_treat: str
    superstition: str

    def to_list(self) -> List[str]:
        return [
            f"Coffee: {self.coffee_order}.",
            f"Reads: {self.reads}.",
            f"Walk: {self.walk}.",
            f"Weekday treat: {self.weekday_treat}.",
            f"Small superstition: {self.superstition}.",
        ]


_TREATS = ["a pastry from the bakery", "a half-pint at the pub",
           "a long bath", "an episode of an old show"]
_SUPERSTITIONS = [
    "never starts work before finishing the coffee",
    "taps the doorframe twice before leaving",
    "keeps a lucky coin in the left pocket",
    "won't schedule anything important on a Friday",
]


def build_habits(rng: random.Random) -> Habits:
    """A deterministic set of small habits."""
    return Habits(
        coffee_order=rng.choice(_COFFEES),
        reads=rng.choice(_PAPERS),
        walk=rng.choice(_WALKS),
        weekday_treat=rng.choice(_TREATS),
        superstition=rng.choice(_SUPERSTITIONS),
    )


def routine_to_text(blocks: List[RoutineBlock]) -> str:
    """Render the routine as a readable timetable."""
    lines = ["DAILY ROUTINE"]
    for block in blocks:
        lines.append(f"  {block.start_hour:02d}:00-{block.end_hour:02d}:00  "
                     f"{block.activity} ({block.location})")
    return "\n".join(lines)


def where_at(blocks: List[RoutineBlock], hour: int) -> Optional[RoutineBlock]:
    """The routine block covering a given hour of the day, if any."""
    if not 0 <= hour <= 23:
        raise HabitsError("hour must be 0-23")
    for block in blocks:
        if block.covers(hour):
            return block
    return None
