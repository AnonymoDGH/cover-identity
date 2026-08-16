"""Exposure-risk assessment for cover identities.

Every legend has weak points: a footprint that is too loud, a timeline
with gaps, a network with no one who would actually vouch. This module
scores an identity plus its supporting material and produces a risk
report with concrete, actionable findings.

The model is deliberately simple and transparent -- a weighted sum of
named factors, each scored 0..1, so a handler can see exactly why a
legend got its rating and fix the worst factor first.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from . import consistency as cons
from . import network as net

__all__ = [
    "RISK_WEIGHTS",
    "score_consistency",
    "score_footprint",
    "score_network",
    "score_paper_trail",
    "assess",
    "risk_band",
]

#: How much each factor contributes to the overall exposure score.
RISK_WEIGHTS: Dict[str, float] = {
    "consistency": 0.35,
    "footprint": 0.25,
    "network": 0.20,
    "paper_trail": 0.20,
}


def score_consistency(identity: Dict, today=None) -> float:
    """0 (clean) to 1 (many errors), from the consistency audit.

    Pass the same reference date the identity was built against, or the
    age check runs against the real today and flags a phantom mismatch.
    """
    findings = cons.audit(identity, today=today)
    errors = sum(1 for f in findings if f.severity == cons.Severity.ERROR)
    warns = sum(1 for f in findings if f.severity == cons.Severity.WARN)
    raw = errors * 0.5 + warns * 0.15
    return min(1.0, raw)


def score_footprint(footprint: Optional[Dict]) -> float:
    """Score the digital footprint. Too loud or too silent both cost.

    A sparse, boring footprint is safest. Zero platforms is suspicious;
    a huge follower count is worse.
    """
    if not footprint:
        return 0.6  # no footprint at all is itself a red flag
    profiles = footprint.get("profiles", [])
    followers = sum(p.get("followers", 0) for p in profiles)
    if not profiles:
        return 0.5
    if followers > 500:
        return 0.9
    if followers > 200:
        return 0.6
    return 0.2


def score_network(network: Optional[List[Dict]]) -> float:
    """Score the social web. No vouch-worthy contacts is risky."""
    if not network:
        return 0.7
    vouch = net.vouch_list(network, threshold=0.5)
    if not vouch:
        return 0.6
    if len(vouch) == 1:
        return 0.35
    return 0.15


def score_paper_trail(wallet: Optional[List[Dict]]) -> float:
    """Score the physical paper trail. Missing documents cost."""
    if not wallet:
        return 0.7
    kinds = {d.get("kind") for d in wallet}
    expected = {"library_card", "utility_bill", "work_badge"}
    missing = expected - kinds
    return min(1.0, 0.15 + 0.2 * len(missing))


def assess(identity: Dict,
           footprint: Optional[Dict] = None,
           network: Optional[List[Dict]] = None,
           wallet: Optional[List[Dict]] = None,
           today=None) -> Dict:
    """Produce a full exposure-risk report for a legend.

    Returns a dict with per-factor scores, the weighted total (0..1), a
    human-readable band, and the single worst factor to fix first.
    """
    factors = {
        "consistency": score_consistency(identity, today=today),
        "footprint": score_footprint(footprint),
        "network": score_network(network),
        "paper_trail": score_paper_trail(wallet),
    }
    total = sum(RISK_WEIGHTS[k] * factors[k] for k in factors)
    worst = max(factors, key=lambda k: factors[k] * RISK_WEIGHTS[k])
    return {
        "factors": factors,
        "total": round(total, 3),
        "band": risk_band(total),
        "worst_factor": worst,
    }


def risk_band(total: float) -> str:
    """Map a 0..1 total to a human-readable risk band."""
    if total < 0.25:
        return "solid"
    if total < 0.5:
        return "workable"
    if total < 0.75:
        return "shaky"
    return "burn-risk"
