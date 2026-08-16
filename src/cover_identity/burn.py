"""Compromise response planning for cover identities.

The time to decide what to do when a legend burns is before it burns.
This module builds a standing response plan: a graded set of actions from
"lay low" to "full evacuation", the triggers that escalate between them,
and a checklist of what to destroy, notify, and abandon at each level.

The plan is deterministic and generic -- it describes procedure, not real
places or people -- so it can be attached to any dossier and rehearsed.
escalate() walks the plan upward as conditions worsen, and the current
level carries exactly the actions that level demands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "BurnError",
    "LEVELS",
    "BurnLevel",
    "BurnPlan",
    "default_plan",
]


class BurnError(ValueError):
    """Raised for burn-plan usage problems."""


@dataclass(frozen=True)
class BurnLevel:
    """One escalation level of the response plan."""

    name: str
    trigger: str
    actions: List[str]
    destroy: List[str]
    notify: List[str]


#: The graded response levels, from mildest to most severe.
LEVELS: List[BurnLevel] = [
    BurnLevel(
        name="lay-low",
        trigger="a minor inconsistency is noticed by someone unimportant",
        actions=["stop initiating contact", "keep routines exactly normal",
                 "observe for a second signal"],
        destroy=[],
        notify=[],
    ),
    BurnLevel(
        name="soft-freeze",
        trigger="someone asks pointed questions about the legend's past",
        actions=["cancel upcoming sensitive meetings", "switch to the backup phone",
                 "review the legend for the exposed thread"],
        destroy=["the primary notebook", "recent receipts"],
        notify=["the handler, by the pre-arranged signal"],
    ),
    BurnLevel(
        name="hard-freeze",
        trigger="a third party demonstrates knowledge the legend never shared",
        actions=["stop all operations immediately", "move to the fallback address",
                 "run the surveillance-detection route before any contact"],
        destroy=["the work badge", "the paper trail wallet", "the signal-site marks"],
        notify=["the handler", "any contact who knows the cover name"],
    ),
    BurnLevel(
        name="evacuate",
        trigger="the legend is directly challenged or the operator is followed",
        actions=["leave the area by the pre-planned route", "assume all "
                 "communications are watched", "switch fully to the next legend"],
        destroy=["everything at the primary address", "the dead-drop contents",
                 "all physical documents"],
        notify=["the handler, once, by the emergency channel"],
    ),
]


class BurnPlan:
    """A standing compromise-response plan with a current level."""

    def __init__(self, levels: Optional[List[BurnLevel]] = None) -> None:
        self._levels = list(LEVELS) if levels is None else list(levels)
        if not self._levels:
            raise BurnError("a burn plan needs at least one level")
        self._index = 0

    @property
    def current(self) -> BurnLevel:
        return self._levels[self._index]

    @property
    def index(self) -> int:
        return self._index

    def escalate(self, steps: int = 1) -> BurnLevel:
        """Move up the plan by the given number of levels.

        Escalating past the top level stays at the top (you cannot be more
        burned than evacuated). Returns the new current level.
        """
        if steps < 1:
            raise BurnError("steps must be >= 1")
        self._index = min(self._index + steps, len(self._levels) - 1)
        return self.current

    def reset(self) -> None:
        """Return to the mildest level (used after a false alarm)."""
        self._index = 0

    def level_names(self) -> List[str]:
        return [level.name for level in self._levels]

    def actions_at(self, level_name: str) -> List[str]:
        """The actions required at a named level."""
        for level in self._levels:
            if level.name == level_name:
                return list(level.actions)
        raise BurnError(f"no level named {level_name!r}")

    def cumulative_destroy(self) -> List[str]:
        """Everything that must be destroyed up to and including the current level."""
        result: List[str] = []
        for level in self._levels[:self._index + 1]:
            for item in level.destroy:
                if item not in result:
                    result.append(item)
        return result

    def to_dict(self) -> Dict:
        """Serialize the plan and its current state."""
        return {
            "levels": [
                {"name": l.name, "trigger": l.trigger, "actions": l.actions,
                 "destroy": l.destroy, "notify": l.notify}
                for l in self._levels
            ],
            "current_index": self._index,
            "current": self.current.name,
        }


def default_plan() -> BurnPlan:
    """A fresh plan at the mildest level, using the standard levels."""
    return BurnPlan()
