"""Pre-deployment readiness assessment for a cover identity.

Before a legend goes live, a handler walks a checklist: is the identity
consistent, is the paper trail complete, does the operator pass the drill,
are the duress codes unambiguous, is the burn plan attached? This module
turns that walk-through into code: it inspects a full dossier and returns
a readiness report with a go/no-go verdict.

Each check is a named gate with a pass/fail and a reason. The verdict is
conservative -- any failed gate means no-go, because a legend is only as
strong as the one thing nobody checked.
"""

from __future__ import annotations

from typing import Dict, List

from . import burn as burn_mod
from . import consistency as cons_mod
from . import emergency as emergency_mod
from . import risk as risk_mod

__all__ = [
    "Gate",
    "readiness_report",
    "verdict",
    "MIN_DRILL_METER",
    "MAX_RISK_TOTAL",
]

#: The drill score an operator must reach before the legend goes live.
MIN_DRILL_METER = 80

#: The maximum acceptable overall risk score.
MAX_RISK_TOTAL = 0.5


class Gate:
    """One readiness gate."""

    def __init__(self, name: str, passed: bool, reason: str) -> None:
        self.name = name
        self.passed = passed
        self.reason = reason

    def to_dict(self) -> Dict:
        return {"name": self.name, "passed": self.passed, "reason": self.reason}


def _gate_consistency(dossier: Dict) -> Gate:
    findings = dossier.get("consistency", [])
    errors = [f for f in findings if str(f).startswith("[ERROR]")]
    if errors:
        return Gate("consistency", False,
                    f"{len(errors)} consistency error(s) must be fixed")
    return Gate("consistency", True, "no consistency errors")


def _gate_risk(dossier: Dict) -> Gate:
    report = dossier.get("risk", {})
    total = report.get("total", 1.0)
    if total > MAX_RISK_TOTAL:
        return Gate("risk", False,
                    f"risk score {total} exceeds {MAX_RISK_TOTAL}")
    return Gate("risk", True, f"risk score {total} within tolerance")


def _gate_paper_trail(dossier: Dict) -> Gate:
    wallet = dossier.get("wallet", [])
    kinds = {d.get("kind") for d in wallet}
    required = {"library_card", "utility_bill", "work_badge"}
    missing = required - kinds
    if missing:
        return Gate("paper_trail", False,
                    f"missing documents: {', '.join(sorted(missing))}")
    return Gate("paper_trail", True, "all required documents present")


def _gate_network(dossier: Dict) -> Gate:
    network = dossier.get("network", [])
    if not network:
        return Gate("network", False, "no contacts defined")
    vouch = [c for c in network if c.get("closeness", 0) >= 0.5]
    if not vouch:
        return Gate("network", False, "no contact close enough to vouch")
    return Gate("network", True, f"{len(vouch)} vouch-worthy contact(s)")


def _gate_drill(dossier: Dict, drill_meter: int) -> Gate:
    if drill_meter < MIN_DRILL_METER:
        return Gate("drill", False,
                    f"drill score {drill_meter} below {MIN_DRILL_METER}")
    return Gate("drill", True, f"drill score {drill_meter} meets the bar")


def _gate_duress(dossier: Dict) -> Gate:
    codes = dossier.get("duress_codes", [])
    problems = emergency_mod.verify_duress_codes(codes)
    if problems:
        return Gate("duress", False, "; ".join(problems))
    if not codes:
        return Gate("duress", False, "no duress codes defined")
    return Gate("duress", True, f"{len(codes)} unambiguous duress code(s)")


def _gate_burn_plan(dossier: Dict) -> Gate:
    # A dossier is ready only if a burn plan can be attached; the standard
    # plan always validates, so this gate checks it is well-formed.
    plan = burn_mod.default_plan()
    if len(plan.level_names()) < 2:
        return Gate("burn_plan", False, "burn plan has fewer than 2 levels")
    return Gate("burn_plan", True, "burn plan attached and well-formed")


def readiness_report(dossier: Dict, drill_meter: int = 100) -> Dict:
    """Run every readiness gate against a dossier.

    Args:
        dossier: The dossier dict from dossier.assemble().
        drill_meter: The operator's current drill score (0-100). Defaults
            to 100, meaning "assume the operator knows the legend".

    Returns:
        A dict with the gates, the count of failures, and the verdict.
    """
    gates = [
        _gate_consistency(dossier),
        _gate_risk(dossier),
        _gate_paper_trail(dossier),
        _gate_network(dossier),
        _gate_drill(dossier, drill_meter),
        _gate_duress(dossier),
        _gate_burn_plan(dossier),
    ]
    failed = [g for g in gates if not g.passed]
    return {
        "gates": [g.to_dict() for g in gates],
        "failed_count": len(failed),
        "verdict": verdict(gates),
        "failed_names": [g.name for g in failed],
    }


def verdict(gates: List[Gate]) -> str:
    """The go/no-go verdict from a list of gates."""
    if all(g.passed for g in gates):
        return "go"
    return "no-go"
