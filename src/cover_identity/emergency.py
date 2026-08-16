"""Emergency protocols and duress signaling for a cover identity.

When things go wrong, the operator needs pre-agreed signals and steps,
not inspiration. This module provides two things: a duress-code generator
that produces innocuous-sounding phrases with hidden meanings, and an
emergency protocol builder that lays out the first minutes after a
compromise in a fixed, rehearsed order.

Duress codes are designed to sound completely normal to anyone listening
-- a comment about the weather, a question about a meal -- while carrying
a specific meaning to the person who knows the code. The module verifies
that no two codes share a phrase, because an ambiguous duress signal is
worse than none.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "EmergencyError",
    "DuressCode",
    "EmergencyStep",
    "build_duress_codes",
    "build_emergency_protocol",
    "protocol_to_text",
    "verify_duress_codes",
]


class EmergencyError(ValueError):
    """Raised for emergency-protocol usage problems."""


@dataclass(frozen=True)
class DuressCode:
    """An innocuous phrase with a hidden emergency meaning."""

    phrase: str
    meaning: str
    channel: str   # spoken, message, or both


_PHRASES: List[str] = [
    "did you water the plants",
    "the weather turned cold",
    "I left the oven on",
    "my cousin is visiting",
    "the match was cancelled",
    "I think I lost my keys",
    "the soup needs more salt",
    "the train was late again",
]
_MEANINGS: List[str] = [
    "I am under pressure; act normal and alert the handler",
    "abort the meeting; do not come to the location",
    "I am being followed; use the backup route",
    "compromised; begin the evacuation plan",
]


def build_duress_codes(rng: random.Random, count: int = 3) -> List[DuressCode]:
    """A deterministic set of duress codes with unique phrases and meanings."""
    if count < 1:
        raise EmergencyError("count must be >= 1")
    count = min(count, len(_MEANINGS))
    phrases = rng.sample(_PHRASES, count)
    meanings = rng.sample(_MEANINGS, count)
    codes: List[DuressCode] = []
    for phrase, meaning in zip(phrases, meanings):
        codes.append(DuressCode(
            phrase=phrase,
            meaning=meaning,
            channel=rng.choice(["spoken", "message", "both"]),
        ))
    return codes


def verify_duress_codes(codes: List[DuressCode]) -> List[str]:
    """Check a set of duress codes for ambiguity. Returns problems."""
    problems: List[str] = []
    phrases = [c.phrase for c in codes]
    meanings = [c.meaning for c in codes]
    if len(phrases) != len(set(phrases)):
        problems.append("two codes share the same phrase")
    if len(meanings) != len(set(meanings)):
        problems.append("two codes share the same meaning")
    for code in codes:
        if len(code.phrase.split()) < 3:
            problems.append(f"phrase {code.phrase!r} is too short to sound natural")
    return problems


@dataclass(frozen=True)
class EmergencyStep:
    """One ordered action in the emergency protocol."""

    order: int
    action: str
    within: str   # the time window to complete it


_STEPS: List[tuple] = [
    ("stop and breathe; confirm you are not in immediate danger", "10 seconds"),
    ("signal the duress code to the nearest contact", "1 minute"),
    ("move to the pre-planned safe location", "15 minutes"),
    ("destroy or abandon anything linking you to the legend", "30 minutes"),
    ("contact the handler by the emergency channel, once", "1 hour"),
    ("go quiet and wait for instructions; do not improvise", "until contacted"),
]


def build_emergency_protocol() -> List[EmergencyStep]:
    """The standard ordered emergency protocol."""
    return [EmergencyStep(order=i + 1, action=action, within=within)
            for i, (action, within) in enumerate(_STEPS)]


def protocol_to_text(steps: List[EmergencyStep]) -> str:
    """Render the protocol as a numbered, readable list."""
    lines = ["EMERGENCY PROTOCOL"]
    for step in steps:
        lines.append(f"  {step.order}. {step.action} (within {step.within})")
    return "\n".join(lines)
