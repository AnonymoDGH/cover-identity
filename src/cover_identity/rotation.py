"""Legend lifecycle and rotation scheduling.

Every cover has a shelf life. The longer a legend runs, the more surface
it accumulates -- more people who know it, more records, more chances to
slip. This module models that lifecycle: each legend gets an activation
date, an expected expiry, and a status. A scheduler then decides which
legend to run next and when to retire the current one.

The model is deliberately conservative: legends expire on a fixed horizon
by default, and any consistency error or high risk score shortens the
horizon. Rotation is deterministic under a seed so two handlers agree on
the schedule.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "RotationError",
    "Status",
    "LegendSlot",
    "RotationSchedule",
    "default_horizon_days",
    "effective_horizon_days",
]

#: Default run length for a legend with no problems.
DEFAULT_HORIZON_DAYS = 180

#: Days shaved off the horizon per consistency error / per 0.1 risk.
_ERROR_PENALTY_DAYS = 30
_RISK_PENALTY_DAYS = 40


class RotationError(ValueError):
    """Raised for rotation-scheduling usage problems."""


class Status:
    """Legend lifecycle statuses."""

    DORMANT = "dormant"      # built but never run
    ACTIVE = "active"        # currently in use
    RETIRED = "retired"      # run and then stood down
    BURNED = "burned"        # compromised; never reuse


@dataclass
class LegendSlot:
    """One legend's place in the rotation."""

    name: str
    status: str = Status.DORMANT
    activated: Optional[dt.date] = None
    expires: Optional[dt.date] = None
    runs: int = 0

    @property
    def is_runnable(self) -> bool:
        """A legend can run unless it is burned or already active."""
        return self.status in (Status.DORMANT, Status.RETIRED)


class RotationSchedule:
    """Manages which legend runs and when it stands down."""

    def __init__(self) -> None:
        self._slots: Dict[str, LegendSlot] = {}

    def register(self, name: str) -> LegendSlot:
        """Register a new dormant legend."""
        key = name.strip()
        if not key:
            raise RotationError("legend name must not be empty")
        if key in self._slots:
            raise RotationError(f"legend {key!r} already registered")
        slot = LegendSlot(name=key)
        self._slots[key] = slot
        return slot

    def get(self, name: str) -> LegendSlot:
        if name not in self._slots:
            raise RotationError(f"no legend named {name!r}")
        return self._slots[name]

    def activate(self, name: str, today: dt.date,
                 horizon_days: Optional[int] = None) -> LegendSlot:
        """Put a legend into rotation.

        Only one legend may be active at a time; activating a second
        raises RotationError. Burned legends can never be activated.
        """
        slot = self.get(name)
        if slot.status == Status.BURNED:
            raise RotationError(f"legend {name!r} is burned; never reuse it")
        current = self.active()
        if current is not None and current.name != name:
            raise RotationError(
                f"legend {current.name!r} is already active; retire it first")
        horizon = horizon_days if horizon_days is not None else DEFAULT_HORIZON_DAYS
        slot.status = Status.ACTIVE
        slot.activated = today
        slot.expires = today + dt.timedelta(days=horizon)
        slot.runs += 1
        return slot

    def retire(self, name: str) -> LegendSlot:
        """Stand down the active legend so another can run."""
        slot = self.get(name)
        if slot.status != Status.ACTIVE:
            raise RotationError(f"legend {name!r} is not active")
        slot.status = Status.RETIRED
        slot.expires = None
        return slot

    def burn(self, name: str) -> LegendSlot:
        """Mark a legend compromised. It can never run again."""
        slot = self.get(name)
        slot.status = Status.BURNED
        slot.expires = None
        return slot

    def active(self) -> Optional[LegendSlot]:
        """The currently active legend, if any."""
        for slot in self._slots.values():
            if slot.status == Status.ACTIVE:
                return slot
        return None

    def next_runnable(self) -> Optional[LegendSlot]:
        """The runnable legend with the fewest prior runs (fresh first)."""
        runnable = [s for s in self._slots.values() if s.is_runnable]
        if not runnable:
            return None
        return min(runnable, key=lambda s: (s.runs, s.name))

    def due_for_rotation(self, today: dt.date) -> List[LegendSlot]:
        """Active legends whose expiry has passed."""
        return [s for s in self._slots.values()
                if s.status == Status.ACTIVE and s.expires is not None
                and s.expires <= today]

    def names(self) -> List[str]:
        return sorted(self._slots)

    def __len__(self) -> int:
        return len(self._slots)


def default_horizon_days() -> int:
    """The standard run length for a clean legend."""
    return DEFAULT_HORIZON_DAYS


def effective_horizon_days(error_count: int, risk_total: float) -> int:
    """Shorten the horizon based on consistency errors and risk.

    More problems -> shorter run. The floor is 30 days: a legend this
    troubled should be rotated quickly, not abandoned mid-operation.
    """
    if error_count < 0:
        raise RotationError("error_count must be >= 0")
    if not 0.0 <= risk_total <= 1.0:
        raise RotationError("risk_total must be in [0, 1]")
    penalty = error_count * _ERROR_PENALTY_DAYS
    penalty += int(risk_total * 10) * (_RISK_PENALTY_DAYS // 10)
    return max(30, DEFAULT_HORIZON_DAYS - penalty)
