"""Pre-action checklists for operating a cover identity.

Checklists beat memory. Before a meeting, before a trip, before a period
of heightened risk, the operator should walk a fixed list of checks --
documents on hand, story rehearsed, signal site clear, exit route known.
This module defines those checklists as data, tracks which items are
done, and refuses to report "ready" while any required item is unchecked.

The lists are deliberately short. A twenty-item checklist does not get
walked; a six-item one does. Each checklist names its purpose and the
consequence of skipping it, so the operator knows why each item exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "ChecklistError",
    "ChecklistItem",
    "Checklist",
    "CHECKLISTS",
    "get_checklist",
]


class ChecklistError(ValueError):
    """Raised for checklist usage problems."""


@dataclass(frozen=True)
class ChecklistItem:
    """One check to perform."""

    text: str
    required: bool
    why: str


class Checklist:
    """A named checklist with per-item completion state."""

    def __init__(self, name: str, purpose: str,
                 items: List[ChecklistItem]) -> None:
        if not items:
            raise ChecklistError("a checklist needs at least one item")
        self.name = name
        self.purpose = purpose
        self._items = list(items)
        self._done: Dict[int, bool] = {i: False for i in range(len(items))}

    def __len__(self) -> int:
        return len(self._items)

    def item(self, index: int) -> ChecklistItem:
        if not 0 <= index < len(self._items):
            raise ChecklistError(f"no item {index}")
        return self._items[index]

    def check(self, index: int) -> None:
        """Mark an item done."""
        self.item(index)
        self._done[index] = True

    def uncheck(self, index: int) -> None:
        self.item(index)
        self._done[index] = False

    def is_done(self, index: int) -> bool:
        self.item(index)
        return self._done[index]

    def progress(self) -> Dict:
        done = sum(1 for flag in self._done.values() if flag)
        return {"done": done, "total": len(self._items),
                "complete": done == len(self._items)}

    def ready(self) -> bool:
        """True only when every REQUIRED item is checked.

        Optional items do not block readiness, but required ones all do.
        """
        for i, item in enumerate(self._items):
            if item.required and not self._done[i]:
                return False
        return True

    def missing_required(self) -> List[str]:
        """The text of required items still unchecked."""
        return [item.text for i, item in enumerate(self._items)
                if item.required and not self._done[i]]

    def to_text(self) -> str:
        lines = [f"CHECKLIST: {self.name} — {self.purpose}"]
        for i, item in enumerate(self._items):
            mark = "[x]" if self._done[i] else "[ ]"
            req = "" if item.required else " (optional)"
            lines.append(f"  {mark} {item.text}{req}")
        return "\n".join(lines)


#: The standard checklists, keyed by name.
CHECKLISTS: Dict[str, Dict] = {
    "pre-meeting": {
        "purpose": "before any face-to-face contact",
        "items": [
            ("documents match the legend", True,
             "a mismatch here burns the meeting"),
            ("story for the last 24 hours rehearsed", True,
             "the first question is usually 'what have you been up to'"),
            ("exit route from the venue known", True,
             "you must be able to leave without thinking"),
            ("signal site checked on the way in", False,
             "confirms no one arrived before you"),
            ("duress code fresh in memory", True,
             "you may need it with no time to recall"),
        ],
    },
    "pre-travel": {
        "purpose": "before any journey under the legend",
        "items": [
            ("travel documents consistent with the destination", True,
             "a ticket to a place the legend has never been is a tell"),
            ("reason for travel matches the cover story", True,
             "you will be asked why, casually, at least once"),
            ("fallback route planned", False,
             "main roads are where checks happen"),
            ("contact schedule adjusted for absence", True,
             "a missed check-in while travelling reads as trouble"),
        ],
    },
    "post-incident": {
        "purpose": "after anything unexpected, before resuming routine",
        "items": [
            ("write down exactly what happened, while fresh", True,
             "memory degrades within hours"),
            ("check whether any legend detail was exposed", True,
             "exposed details must be retired or patched"),
            ("confirm no one was followed home", True,
             "run the SDR before assuming you are clean"),
            ("log the incident in the debrief", False,
             "builds the record for the next review"),
        ],
    },
}


def get_checklist(name: str) -> Checklist:
    """Build a fresh, unchecked instance of a named checklist.

    Raises:
        ChecklistError: If the name is unknown.
    """
    if name not in CHECKLISTS:
        raise ChecklistError(
            f"unknown checklist {name!r}; choose from {sorted(CHECKLISTS)}")
    spec = CHECKLISTS[name]
    items = [ChecklistItem(text=text, required=required, why=why)
             for text, required, why in spec["items"]]
    return Checklist(name=name, purpose=spec["purpose"], items=items)
