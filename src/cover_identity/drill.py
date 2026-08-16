"""Memorization drill for cover identities.

A legend you cannot recite under pressure is a legend that will burn.
This module turns an identity into a scored drill: ask the operator each
question, grade the answer (exact, fuzzy, or wrong), and track a running
"burn meter" -- a 0..100 score of how solidly the cover knows their own
story.

Grading is forgiving about case and punctuation but strict about facts.
Fuzzy credit is given when the answer contains the key token (a name, a
year, a plate), because under stress people paraphrase. The drill returns
a full result record so a handler can log progress across sessions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

__all__ = [
    "Grade",
    "DrillItem",
    "DrillResult",
    "normalize",
    "grade_answer",
    "build_drill",
    "run_drill",
    "burn_meter",
    "weakest_items",
]


class Grade:
    """Answer grades, from full marks to a miss."""

    EXACT = "exact"
    FUZZY = "fuzzy"
    WRONG = "wrong"

    POINTS = {EXACT: 1.0, FUZZY: 0.5, WRONG: 0.0}


@dataclass(frozen=True)
class DrillItem:
    """One question in the drill."""

    prompt: str
    answer: str
    category: str = "general"


@dataclass
class DrillResult:
    """The outcome of one drill session."""

    items: List[Dict] = field(default_factory=list)
    score: float = 0.0
    meter: int = 0

    @property
    def passed(self) -> bool:
        """A cover passes at 80 or above on the burn meter."""
        return self.meter >= 80


def normalize(text: str) -> str:
    """Lowercase and strip punctuation/whitespace for comparison."""
    return re.sub(r"[^a-z0-9 ]", "", str(text).lower()).strip()


def _key_tokens(answer: str) -> List[str]:
    """The meaningful tokens of an answer, longest first."""
    tokens = [t for t in normalize(answer).split() if len(t) >= 2]
    return sorted(tokens, key=len, reverse=True)


def grade_answer(expected: str, given: str) -> str:
    """Grade a given answer against the expected one.

    Exact (after normalization) -> EXACT. Contains the longest key token
    -> FUZZY. Otherwise -> WRONG.
    """
    exp = normalize(expected)
    got = normalize(given)
    if not got:
        return Grade.WRONG
    if got == exp:
        return Grade.EXACT
    for token in _key_tokens(expected):
        if token in got:
            return Grade.FUZZY
    return Grade.WRONG


def build_drill(identity: Dict) -> List[DrillItem]:
    """Turn an identity into a drill covering basics, anchors, and timeline."""
    items: List[DrillItem] = [
        DrillItem("Full name", identity.get("name", ""), "basics"),
        DrillItem("Date of birth", identity.get("date_of_birth", ""), "basics"),
        DrillItem("Occupation", identity.get("occupation", ""), "basics"),
        DrillItem("Employer", identity.get("employer", ""), "basics"),
        DrillItem("Address", identity.get("address", ""), "basics"),
    ]
    for q in identity.get("cover_questions", []):
        items.append(DrillItem(f"Your {q['question']}", q["answer"], "anchor"))
    timeline = identity.get("timeline", [])
    if timeline:
        born = next((e for e in timeline if e["event"] == "born"), None)
        if born:
            items.append(DrillItem("What year were you born?",
                                   str(born["year"]), "timeline"))
        present = next((e for e in timeline if e["event"] == "present"), None)
        if present:
            items.append(DrillItem("What do you do now?",
                                   present["detail"], "timeline"))
    return items


def run_drill(identity: Dict,
              answer_fn: Callable[[str], str]) -> DrillResult:
    """Run the drill, pulling each answer from answer_fn(prompt).

    answer_fn is called once per item with the prompt; it should return the
    operator's spoken answer. In tests, pass a canned function.
    """
    result = DrillResult()
    for item in build_drill(identity):
        given = answer_fn(item.prompt)
        grade = grade_answer(item.answer, given)
        result.items.append({
            "prompt": item.prompt,
            "expected": item.answer,
            "given": given,
            "grade": grade,
            "category": item.category,
        })
    result.score = sum(Grade.POINTS[i["grade"]] for i in result.items)
    result.meter = burn_meter(result.items)
    return result


def burn_meter(items: Sequence[Dict]) -> int:
    """Convert graded items into a 0..100 burn meter.

    Weighted so anchor and timeline questions count a little more than the
    basics -- those are the ones an interrogator presses on.
    """
    if not items:
        return 0
    weights = {"anchor": 1.5, "timeline": 1.25, "basics": 1.0}
    total = 0.0
    earned = 0.0
    for item in items:
        w = weights.get(item.get("category", "basics"), 1.0)
        total += w
        earned += w * Grade.POINTS[item["grade"]]
    return int(round(100 * earned / total)) if total else 0


def weakest_items(result: DrillResult, n: int = 3) -> List[Dict]:
    """The n lowest-scoring items, for targeted re-drilling."""
    ranked = sorted(result.items, key=lambda i: Grade.POINTS[i["grade"]])
    return ranked[:n]
