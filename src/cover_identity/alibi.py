"""Alibi construction for a cover identity.

When someone asks "where were you at nine on Tuesday?", the answer has to
be instant, boring, and consistent with everything else the legend says.
This module builds alibis out of the legend's own routine, habits, and
network, then verifies them: an alibi that puts the cover somewhere the
routine says they are not, or that names a contact who does not exist, is
flagged before it is ever spoken.

An alibi is a list of claims, each pinned to an hour, a place, and
optionally a witness. verify_alibi() checks every claim against the
routine blocks and the network, and returns the contradictions. The best
alibi is the one that needs no invention at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import habits

__all__ = [
    "AlibiError",
    "AlibiClaim",
    "Alibi",
    "claim_from_routine",
    "build_alibi",
    "verify_alibi",
    "alibi_to_text",
]


class AlibiError(ValueError):
    """Raised for alibi usage problems."""


@dataclass(frozen=True)
class AlibiClaim:
    """One hour-pinned statement of where the cover was."""

    hour: int
    place: str
    activity: str
    witness: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0 <= self.hour <= 23:
            raise AlibiError("hour must be 0-23")


@dataclass
class Alibi:
    """A set of claims covering a span of hours."""

    day: str
    claims: List[AlibiClaim] = field(default_factory=list)

    def add(self, claim: AlibiClaim) -> None:
        if any(c.hour == claim.hour for c in self.claims):
            raise AlibiError(f"two claims for hour {claim.hour}")
        self.claims.append(claim)
        self.claims.sort(key=lambda c: c.hour)

    def hours_covered(self) -> List[int]:
        return [c.hour for c in self.claims]


def claim_from_routine(blocks: List[habits.RoutineBlock], hour: int,
                       witness: Optional[str] = None) -> AlibiClaim:
    """Build a claim for an hour straight out of the routine.

    This is the safest alibi: it cannot contradict the legend because it
    is the legend.
    """
    block = habits.where_at(blocks, hour)
    if block is None:
        raise AlibiError(f"no routine block covers hour {hour}")
    return AlibiClaim(hour=hour, place=block.location,
                      activity=block.activity, witness=witness)


def build_alibi(day: str, blocks: List[habits.RoutineBlock],
                hours: List[int],
                witnesses: Optional[Dict[int, str]] = None) -> Alibi:
    """Build an alibi for a list of hours from the routine.

    witnesses optionally pins specific hours to a named person.
    """
    witnesses = witnesses or {}
    alibi = Alibi(day=day)
    for hour in hours:
        alibi.add(claim_from_routine(blocks, hour, witnesses.get(hour)))
    return alibi


def verify_alibi(alibi: Alibi, blocks: List[habits.RoutineBlock],
                 network: Optional[List[Dict]] = None) -> List[str]:
    """Check an alibi against the routine and the network.

    Returns a list of contradiction strings; empty means the alibi holds.
    A claim contradicts the routine if its place differs from the routine
    block's location for that hour, and contradicts the network if it names
    a witness who is not a known contact.
    """
    problems: List[str] = []
    known = {c["name"] for c in (network or [])}
    for claim in alibi.claims:
        block = habits.where_at(blocks, claim.hour)
        if block is None:
            problems.append(
                f"hour {claim.hour}: no routine block (claim: {claim.place})")
            continue
        if claim.place != block.location:
            problems.append(
                f"hour {claim.hour}: alibi says {claim.place!r} but routine "
                f"says {block.location!r}")
        if claim.witness is not None and known and claim.witness not in known:
            problems.append(
                f"hour {claim.hour}: witness {claim.witness!r} is not in the network")
    return problems


def alibi_to_text(alibi: Alibi) -> str:
    """Render an alibi as a speakable statement."""
    lines = [f"ALIBI FOR {alibi.day.upper()}"]
    for claim in alibi.claims:
        witness = f" with {claim.witness}" if claim.witness else ""
        lines.append(f"  {claim.hour:02d}:00 — {claim.activity} at "
                     f"{claim.place}{witness}")
    return "\n".join(lines)
