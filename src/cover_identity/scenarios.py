"""Rehearsal scenarios for practicing a cover identity.

Reading a dossier is not the same as living it. This module generates
short, concrete rehearsal scenarios -- a day in the life, a checkpoint
encounter, a nosy neighbor, a workplace chat -- each built from the
legend's own details so the operator practices the actual story, not a
generic one.

Each scenario names the setting, the other person, the opening line, and
the specific legend facts it is designed to exercise. A handler can run
the operator through several scenarios and grade the responses with the
drill and interrogation modules.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "Scenario",
    "build_scenarios",
    "scenario_to_text",
]


@dataclass(frozen=True)
class Scenario:
    """One rehearsal scene."""

    title: str
    setting: str
    other_person: str
    opening_line: str
    exercises: List[str]   # the legend facts this scene pulls on


def _market_scenario(rng: random.Random, identity: Dict) -> Scenario:
    shop = corpus.pick(rng, corpus.SHOPS)
    return Scenario(
        title="The market encounter",
        setting=f"the stall at {shop}, mid-morning",
        other_person="a vendor who has seen you before",
        opening_line="Back again! Still working at the same place?",
        exercises=["occupation", "employer", "daily routine"],
    )


def _neighbor_scenario(rng: random.Random, identity: Dict) -> Scenario:
    return Scenario(
        title="The nosy neighbor",
        setting="the stairwell of your building, evening",
        other_person="a neighbor who makes small talk",
        opening_line="You keep odd hours. What is it you do, exactly?",
        exercises=["occupation", "address", "how long at the address"],
    )


def _checkpoint_scenario(rng: random.Random, identity: Dict) -> Scenario:
    return Scenario(
        title="The document check",
        setting="a routine ID checkpoint on the road",
        other_person="an official who is bored but thorough",
        opening_line="Papers, please. Where are you headed today?",
        exercises=["name", "date of birth", "address", "destination story"],
    )


def _workplace_scenario(rng: random.Random, identity: Dict) -> Scenario:
    return Scenario(
        title="The workplace chat",
        setting="the break room, lunch",
        other_person="a coworker you barely know",
        opening_line="So where did you grow up? You have an accent.",
        exercises=["backstory origin", "birth town", "accent story"],
    )


def _old_friend_scenario(rng: random.Random, identity: Dict) -> Scenario:
    return Scenario(
        title="The face from the past",
        setting="a cafe, afternoon",
        other_person="someone who claims to know you from before",
        opening_line="It IS you! Don't you remember me? From the old town?",
        exercises=["backstory disruption", "timeline", "the move"],
    )


_BUILDERS = [
    _market_scenario,
    _neighbor_scenario,
    _checkpoint_scenario,
    _workplace_scenario,
    _old_friend_scenario,
]


def build_scenarios(identity: Dict, seed: Optional[int] = None,
                    count: int = 3) -> List[Scenario]:
    """A deterministic set of rehearsal scenarios drawn from the legend."""
    rng = random.Random(seed)
    count = max(1, min(count, len(_BUILDERS)))
    builders = rng.sample(_BUILDERS, count)
    return [builder(rng, identity) for builder in builders]


def scenario_to_text(scenario: Scenario) -> str:
    """Render one scenario as a readable rehearsal card."""
    lines = [
        f"SCENARIO: {scenario.title}",
        f"  setting:  {scenario.setting}",
        f"  person:   {scenario.other_person}",
        f"  opens:    \"{scenario.opening_line}\"",
        f"  exercises: {', '.join(scenario.exercises)}",
    ]
    return "\n".join(lines)
