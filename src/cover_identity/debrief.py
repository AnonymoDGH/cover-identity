"""Post-operation debrief for cover identities.

After a legend is used, the operator should be debriefed: what questions
came up, which answers felt shaky, what details got invented on the fly.
Invented details are the most dangerous kind, because they are not in the
dossier and will be told differently next time.

This module records a debrief as a structured log of moments, classifies
each moment (clean, shaky, invented), and produces a lessons-learned
report that names exactly which legend fields need to be strengthened or
written down before the next run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "DebriefError",
    "Outcome",
    "DebriefMoment",
    "Debrief",
    "lessons_report",
]


class DebriefError(ValueError):
    """Raised for debrief usage problems."""


class Outcome:
    """How a moment went."""

    CLEAN = "clean"        # answered from the legend, no friction
    SHAKY = "shaky"        # answered, but with visible hesitation
    INVENTED = "invented"  # made up a detail that is not in the dossier
    AVOIDED = "avoided"    # dodged the question entirely

    ALL = (CLEAN, SHAKY, INVENTED, AVOIDED)


@dataclass(frozen=True)
class DebriefMoment:
    """One question-and-answer moment from the operation."""

    question: str
    field: str        # which legend field it touched
    outcome: str

    def __post_init__(self) -> None:
        if self.outcome not in Outcome.ALL:
            raise DebriefError(f"unknown outcome {self.outcome!r}")


class Debrief:
    """A structured debrief log for one operation."""

    def __init__(self, legend_name: str) -> None:
        if not legend_name.strip():
            raise DebriefError("legend_name must not be empty")
        self.legend_name = legend_name.strip()
        self._moments: List[DebriefMoment] = []

    def add(self, question: str, field: str, outcome: str) -> DebriefMoment:
        moment = DebriefMoment(question=question, field=field, outcome=outcome)
        self._moments.append(moment)
        return moment

    @property
    def moments(self) -> List[DebriefMoment]:
        return list(self._moments)

    def __len__(self) -> int:
        return len(self._moments)

    def outcome_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {outcome: 0 for outcome in Outcome.ALL}
        for moment in self._moments:
            counts[moment.outcome] += 1
        return counts

    def trouble_fields(self) -> List[str]:
        """Legend fields that produced shaky or invented answers, in order
        of severity (invented first, then shaky)."""
        invented = [m.field for m in self._moments
                    if m.outcome == Outcome.INVENTED]
        shaky = [m.field for m in self._moments
                 if m.outcome == Outcome.SHAKY and m.field not in invented]
        return invented + shaky


def lessons_report(debrief: Debrief) -> Dict:
    """Turn a debrief into an actionable lessons-learned report.

    The report names the fields to fix, suggests whether the legend needs
    a patch (small fixes) or a rebuild (too many invented details), and
    counts how the operation went overall.
    """
    counts = debrief.outcome_counts()
    trouble = debrief.trouble_fields()
    total = len(debrief)
    invented = counts[Outcome.INVENTED]
    if total == 0:
        recommendation = "no data; run the legend before judging it"
    elif invented == 0 and counts[Outcome.SHAKY] == 0:
        recommendation = "legend held; keep it as is"
    elif invented <= 2:
        recommendation = "patch the legend: write down the invented details"
    else:
        recommendation = "rebuild the legend; too many invented threads"
    return {
        "legend": debrief.legend_name,
        "moments": total,
        "counts": counts,
        "trouble_fields": trouble,
        "recommendation": recommendation,
    }
