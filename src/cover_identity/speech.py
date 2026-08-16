"""Verbal camouflage for a cover identity.

What a cover says matters less than how they say it. This module builds
the speech layer of a legend: a small vocabulary of filler phrases,
deflection lines for awkward questions, topics to steer toward and away
from, and a list of things the operator must never say because they tie
back to the real person.

It also scores a sample of speech for "legend leakage" -- words and
patterns that betray the operator's real background. The scoring is
heuristic but concrete, so a handler can run the operator's practice
conversation through it and get a number back.
"""

from __future__ import annotations

import random
import re
from typing import Dict, List, Optional, Sequence

from . import corpus

__all__ = [
    "FILLERS",
    "DEFLECTIONS",
    "NEVER_SAY",
    "build_speech_kit",
    "steer_topics",
    "score_leakage",
    "speech_report",
]

#: Neutral filler phrases that buy thinking time without revealing anything.
FILLERS: List[str] = [
    "let me think about that",
    "funny you should ask",
    "it's been a while, honestly",
    "I never really kept track",
    "you know how it is",
]

#: Deflection lines for questions that press too hard.
DEFLECTIONS: List[str] = [
    "I'd rather not get into it, if you don't mind",
    "that's a long story for another time",
    "why do you ask?",
    "I'm not the interesting one here — tell me about you",
    "ha, you sound like my accountant",
]

#: Patterns that leak the operator's real life. Checked by score_leakage.
NEVER_SAY: List[str] = [
    "my real name",
    "back when I was in the service",
    "my handler",
    "the agency",
    "my previous identity",
    "classified",
    "I can't tell you that",
]


def build_speech_kit(rng: random.Random, identity: Dict) -> Dict:
    """Assemble a deterministic speech kit tuned to one identity.

    The kit includes a few fillers, a few deflections, safe topics drawn
    from the cover's hobbies and job, and danger topics to avoid.
    """
    hobbies = identity.get("hobbies") or corpus.hobby_pair(rng)
    occupation = identity.get("occupation", "work")
    return {
        "fillers": rng.sample(FILLERS, 3),
        "deflections": rng.sample(DEFLECTIONS, 3),
        "safe_topics": [
            f"the details of {hobbies[0]}",
            f"the details of {hobbies[-1]}",
            f"day-to-day {occupation} work",
            "the weather and the neighborhood",
        ],
        "danger_topics": [
            "politics",
            "the operator's childhood before the cover's stated birth town",
            "exact dates and numbers under pressure",
            "anyone's real name",
        ],
        "never_say": list(NEVER_SAY),
    }


def steer_topics(kit: Dict, question: str) -> str:
    """Pick a safe topic to steer toward when a question feels risky.

    Heuristic: if the question mentions a danger topic, return the first
    safe topic; otherwise return a neutral deflection.
    """
    text = question.lower()
    for danger in kit.get("danger_topics", []):
        # Match on the first significant word of the danger topic.
        head = danger.split()[0].lower()
        if head and head in text:
            return kit["safe_topics"][0]
    return kit["deflections"][0]


def score_leakage(text: str, never_say: Optional[Sequence[str]] = None) -> Dict:
    """Score a passage of speech for legend leakage.

    Returns a dict with the count of forbidden phrases found, the list of
    matches, and a 0..1 leakage score (higher is worse).
    """
    forbidden = list(never_say or NEVER_SAY)
    lowered = text.lower()
    matches = [phrase for phrase in forbidden if phrase in lowered]
    # Also flag hedging density: too many hedges reads as rehearsed.
    hedges = len(re.findall(r"\b(um|uh|maybe|perhaps|i guess)\b", lowered))
    words = max(1, len(lowered.split()))
    hedge_density = hedges / words
    score = min(1.0, 0.4 * len(matches) + hedge_density * 2)
    return {
        "matches": matches,
        "match_count": len(matches),
        "hedges": hedges,
        "score": round(score, 3),
    }


def speech_report(kit: Dict, sample: str) -> Dict:
    """Combine a speech kit and a scored sample into one report."""
    leakage = score_leakage(sample, kit.get("never_say"))
    return {
        "kit_topics": len(kit.get("safe_topics", [])),
        "leakage": leakage,
        "clean": leakage["match_count"] == 0,
        "verdict": "clean" if leakage["score"] < 0.2 else
                   ("watch" if leakage["score"] < 0.6 else "burn"),
    }
