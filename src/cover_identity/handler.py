"""Handler dashboard for managing multiple cover identities.

A handler running several legends needs one view: which legend is active,
which are ready, which are due for rotation, and where the risk sits. This
module aggregates dossiers into a single dashboard, combining the rotation
schedule, the readiness gates, and the risk scores into one report.

The dashboard is read-only and deterministic: it does not change any
state, it only summarizes. That makes it safe to render at any time and
easy to test against a fixed set of dossiers.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from . import readiness as readiness_mod
from . import rotation as rotation_mod

__all__ = [
    "HandlerError",
    "HandlerDashboard",
    "dashboard_to_text",
]


class HandlerError(ValueError):
    """Raised for dashboard usage problems."""


class HandlerDashboard:
    """Aggregates several legends into one operational picture."""

    def __init__(self) -> None:
        self._schedule = rotation_mod.RotationSchedule()
        self._dossiers: Dict[str, Dict] = {}

    def add_legend(self, name: str, dossier: Dict) -> None:
        """Register a legend and its dossier."""
        if name in self._dossiers:
            raise HandlerError(f"legend {name!r} already added")
        self._dossiers[name] = dossier
        self._schedule.register(name)

    def activate(self, name: str, today: dt.date,
                 horizon_days: Optional[int] = None) -> None:
        """Put a legend into rotation."""
        if name not in self._dossiers:
            raise HandlerError(f"no legend named {name!r}")
        self._schedule.activate(name, today, horizon_days)

    def retire(self, name: str) -> None:
        self._schedule.retire(name)

    def burn(self, name: str) -> None:
        self._schedule.burn(name)

    @property
    def schedule(self) -> rotation_mod.RotationSchedule:
        return self._schedule

    def readiness(self, name: str, drill_meter: int = 100) -> Dict:
        """The readiness report for one legend."""
        if name not in self._dossiers:
            raise HandlerError(f"no legend named {name!r}")
        return readiness_mod.readiness_report(self._dossiers[name], drill_meter)

    def overview(self, today: dt.date) -> Dict:
        """The full operational picture.

        For each legend: status, risk band, and readiness verdict. Plus
        the active legend and any legends due for rotation.
        """
        rows: List[Dict] = []
        for name in sorted(self._dossiers):
            dossier = self._dossiers[name]
            slot = self._schedule.get(name)
            rows.append({
                "name": name,
                "status": slot.status,
                "risk_band": dossier.get("risk", {}).get("band", "unknown"),
                "risk_total": dossier.get("risk", {}).get("total"),
                "ready": self.readiness(name)["verdict"],
            })
        active = self._schedule.active()
        due = self._schedule.due_for_rotation(today)
        return {
            "legends": rows,
            "active": active.name if active else None,
            "due_for_rotation": [s.name for s in due],
            "total": len(rows),
        }


def dashboard_to_text(dashboard: HandlerDashboard, today: dt.date) -> str:
    """Render the dashboard as a readable status board."""
    overview = dashboard.overview(today)
    lines = ["HANDLER DASHBOARD", "=" * 40]
    for row in overview["legends"]:
        marker = "*" if row["name"] == overview["active"] else " "
        lines.append(f"{marker} {row['name']:<12} {row['status']:<9} "
                     f"risk={row['risk_band']:<10} ready={row['ready']}")
    lines.append("-" * 40)
    lines.append(f"Active: {overview['active'] or '(none)'}")
    if overview["due_for_rotation"]:
        lines.append("Due for rotation: " + ", ".join(overview["due_for_rotation"]))
    else:
        lines.append("Due for rotation: (none)")
    return "\n".join(lines)
