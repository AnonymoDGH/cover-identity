"""Communication schedule and missed-contact escalation.

An operator who goes quiet without explanation looks exactly like an
operator who has been picked up. This module builds the comms layer: a
regular check-in schedule, the escalation ladder when a check-in is
missed, and a log that records each contact so gaps are visible.

The escalation ladder is the heart of it. One missed check-in is a
traffic jam; three is a crisis. The module encodes that gradient
explicitly, with a distinct action at each rung, and the log can compute
the current escalation level from the raw record of contacts.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "CommsError",
    "CheckIn",
    "CommsLog",
    "build_schedule",
    "escalation_for_missed",
    "ESCALATION_LADDER",
]


class CommsError(ValueError):
    """Raised for comms-layer usage problems."""


@dataclass(frozen=True)
class CheckIn:
    """One scheduled contact window."""

    day: str            # weekday name
    time: str           # HH:MM
    channel: str        # how the contact happens
    backup_channel: str


_CHANNELS = ["a short message", "a brief call", "an in-person coffee",
             "a marked post online", "a signal at the agreed site"]
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday", "Sunday"]


def build_schedule(rng, per_week: int = 2) -> List[CheckIn]:
    """A deterministic weekly check-in schedule.

    Spreads the contacts across distinct days so a single bad day does not
    swallow the whole week's contact.
    """
    if per_week < 1:
        raise CommsError("per_week must be >= 1")
    per_week = min(per_week, 7)
    days = rng.sample(_DAYS, per_week)
    schedule: List[CheckIn] = []
    for day in sorted(days, key=_DAYS.index):
        hour = rng.randrange(8, 21)
        minute = rng.choice([0, 15, 30, 45])
        primary = rng.choice(_CHANNELS)
        backup = rng.choice([c for c in _CHANNELS if c != primary])
        schedule.append(CheckIn(
            day=day,
            time=f"{hour:02d}:{minute:02d}",
            channel=primary,
            backup_channel=backup,
        ))
    return schedule


#: Escalation ladder: index = consecutive missed check-ins.
ESCALATION_LADDER: List[Dict] = [
    {"missed": 0, "level": "normal",
     "action": "continue the schedule as agreed"},
    {"missed": 1, "level": "watch",
     "action": "try the backup channel once; observe the signal site"},
    {"missed": 2, "level": "concern",
     "action": "run the soft-freeze steps; alert the handler"},
    {"missed": 3, "level": "alarm",
     "action": "assume compromise; begin hard-freeze; no further contact attempts"},
]


def escalation_for_missed(missed: int) -> Dict:
    """The escalation rung for a given count of consecutive misses."""
    if missed < 0:
        raise CommsError("missed must be >= 0")
    if missed >= len(ESCALATION_LADDER):
        return ESCALATION_LADDER[-1]
    return ESCALATION_LADDER[missed]


class CommsLog:
    """A record of scheduled vs. actual contacts.

    Each entry is a dict with day, scheduled (bool), and made (bool).
    The log computes the current consecutive-miss streak and the matching
    escalation rung.
    """

    def __init__(self) -> None:
        self._entries: List[Dict] = []

    def record(self, day: str, scheduled: bool, made: bool) -> None:
        """Record one contact opportunity."""
        self._entries.append({"day": day, "scheduled": scheduled, "made": made})

    def __len__(self) -> int:
        return len(self._entries)

    def consecutive_misses(self) -> int:
        """Missed scheduled contacts at the tail of the log."""
        streak = 0
        for entry in reversed(self._entries):
            if entry["scheduled"] and not entry["made"]:
                streak += 1
            else:
                break
        return streak

    def current_escalation(self) -> Dict:
        """The escalation rung implied by the log's tail."""
        return escalation_for_missed(self.consecutive_misses())

    def contact_rate(self) -> float:
        """Fraction of scheduled contacts actually made."""
        scheduled = [e for e in self._entries if e["scheduled"]]
        if not scheduled:
            return 1.0
        made = sum(1 for e in scheduled if e["made"])
        return round(made / len(scheduled), 3)
