"""Interrogation stress-testing for cover identities.

The drill module checks whether the operator *knows* the legend. This
module checks whether the legend *survives* being pulled on. It generates
adversarial questions a suspicious interviewer would actually ask --
probing the timeline for gaps, the network for people who do not exist,
the paper trail for documents that do not line up -- and scores how the
legend holds up.

Each probe targets a specific facet and carries a difficulty. The
simulator does not role-play the operator; it produces the probe list and
a scoring rubric so a handler can run the exercise and grade the answers.
"""

from __future__ import annotations

import random
from typing import Callable, Dict, List, Optional

from . import corpus
from . import timeline as tl

__all__ = [
    "Probe",
    "build_probes",
    "run_interrogation",
    "interrogation_report",
]


class Probe:
    """One adversarial question aimed at a facet of the legend."""

    def __init__(self, facet: str, question: str, difficulty: int,
                 tell: str) -> None:
        self.facet = facet        # which part of the legend is under pressure
        self.question = question  # what the interviewer asks
        self.difficulty = difficulty  # 1 (soft) .. 5 (aggressive)
        self.tell = tell          # what a bad answer reveals

    def to_dict(self) -> Dict:
        return {"facet": self.facet, "question": self.question,
                "difficulty": self.difficulty, "tell": self.tell}


def _timeline_probes(identity: Dict, rng: random.Random) -> List[Probe]:
    """Probes that pull on the dated life history."""
    probes: List[Probe] = []
    timeline = identity.get("timeline", [])
    gaps = tl.gap_report(timeline, max_gap=6)
    for gap in gaps[:2]:
        probes.append(Probe(
            "timeline",
            f"What were you doing between {gap['from_year']} and "
            f"{gap['to_year']}?",
            difficulty=4,
            tell="A hesitation here exposes an unexplained gap.",
        ))
    born = next((e for e in timeline if e["event"] == "born"), None)
    if born:
        probes.append(Probe(
            "timeline",
            "Tell me about the town you grew up in. What was it like?",
            difficulty=2,
            tell="Generic answers suggest a fabricated origin.",
        ))
    return probes


def _network_probes(identity: Dict, network: List[Dict],
                    rng: random.Random) -> List[Probe]:
    """Probes that name a contact and watch the reaction."""
    probes: List[Probe] = []
    for contact in network[:2]:
        probes.append(Probe(
            "network",
            f"We spoke with {contact['name']}. They weren't sure they "
            f"knew you. Explain.",
            difficulty=5,
            tell="Not recognizing a named contact burns the web.",
        ))
    if not network:
        probes.append(Probe(
            "network",
            "You don't seem to know anyone around here. Why is that?",
            difficulty=3,
            tell="Isolation is itself suspicious.",
        ))
    return probes


def _paper_probes(identity: Dict, wallet: List[Dict],
                  rng: random.Random) -> List[Probe]:
    """Probes that ask for documents on the spot."""
    probes: List[Probe] = []
    kinds = {d.get("kind") for d in wallet}
    if "work_badge" in kinds:
        probes.append(Probe(
            "paper_trail",
            "Show me your work badge. We'll verify with your employer.",
            difficulty=4,
            tell="A fake badge fails the callback.",
        ))
    if "utility_bill" in kinds:
        probes.append(Probe(
            "paper_trail",
            "What's your current monthly utility bill, roughly?",
            difficulty=2,
            tell="Not knowing your own bill reads as staged.",
        ))
    return probes


def _anchor_probes(identity: Dict, rng: random.Random) -> List[Probe]:
    """Probes that re-ask memory anchors in a different order/wording."""
    probes: List[Probe] = []
    questions = identity.get("cover_questions", [])
    for q in questions[:2]:
        probes.append(Probe(
            "anchor",
            f"Just to confirm — {q['question']}?",
            difficulty=3,
            tell="A mismatch with the earlier answer is a hard tell.",
        ))
    return probes


def build_probes(identity: Dict, network: Optional[List[Dict]] = None,
                 wallet: Optional[List[Dict]] = None,
                 seed: Optional[int] = None,
                 max_probes: int = 8) -> List[Probe]:
    """Assemble a deterministic set of adversarial probes.

    Probes are drawn from every facet and ordered easiest-first, the way
    a real interview escalates.
    """
    rng = random.Random(seed)
    probes: List[Probe] = []
    probes += _timeline_probes(identity, rng)
    probes += _network_probes(identity, network or [], rng)
    probes += _paper_probes(identity, wallet or [], rng)
    probes += _anchor_probes(identity, rng)
    probes.sort(key=lambda p: p.difficulty)
    return probes[:max_probes]


def run_interrogation(identity: Dict,
                      answer_fn: Callable[[str], str],
                      network: Optional[List[Dict]] = None,
                      wallet: Optional[List[Dict]] = None,
                      seed: Optional[int] = None) -> Dict:
    """Run the interrogation, scoring each answer by length and confidence.

    answer_fn receives each probe's question and returns the operator's
    reply. Scoring is heuristic: a reply that is too short, or that hedges
    with filler words, loses points. Returns a full result record.
    """
    probes = build_probes(identity, network, wallet, seed)
    results: List[Dict] = []
    for probe in probes:
        reply = answer_fn(probe.question)
        score = _score_reply(reply, probe)
        results.append({
            **probe.to_dict(),
            "reply": reply,
            "score": score,
        })
    return interrogation_report(results)


_HEDGE_WORDS = {"maybe", "perhaps", "i think", "i guess", "not sure",
                "um", "uh", "probably"}


def _score_reply(reply: str, probe: Probe) -> float:
    """Heuristic 0..1 score for one reply.

    Longer, direct answers score higher; hedging and very short replies
    score lower. Difficulty raises the bar.
    """
    text = reply.strip().lower()
    if not text:
        return 0.0
    base = min(1.0, len(text.split()) / 12.0)
    hedges = sum(1 for w in _HEDGE_WORDS if w in text)
    penalty = 0.15 * hedges + 0.05 * (probe.difficulty - 1)
    return max(0.0, round(base - penalty, 2))


def interrogation_report(results: List[Dict]) -> Dict:
    """Summarize an interrogation: per-facet scores and an overall verdict."""
    if not results:
        return {"probes": 0, "overall": 1.0, "verdict": "no-probes",
                "by_facet": {}, "results": []}
    by_facet: Dict[str, List[float]] = {}
    for r in results:
        by_facet.setdefault(r["facet"], []).append(r["score"])
    facet_avg = {f: round(sum(s) / len(s), 2) for f, s in by_facet.items()}
    overall = round(sum(r["score"] for r in results) / len(results), 2)
    if overall >= 0.7:
        verdict = "holds"
    elif overall >= 0.4:
        verdict = "strained"
    else:
        verdict = "cracks"
    return {
        "probes": len(results),
        "overall": overall,
        "verdict": verdict,
        "by_facet": facet_avg,
        "results": results,
    }
