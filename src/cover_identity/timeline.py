"""Life-timeline generation for cover identities.

A legend without dates is a legend that collapses under the first "so what
were you doing in 2016?" This module builds a dated, internally consistent
life history from a date of birth: schooling, first jobs, moves, and the
present occupation, each pinned to a plausible year.

Every event year is derived from the birth year plus a typical age offset,
with a little seeded jitter so two covers born the same year do not live
identical lives. The result is a list of {year, event, detail} dicts in
chronological order, ready to drop into the identity and to be checked by
consistency.check_timeline.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "build_timeline",
    "timeline_to_text",
    "gap_report",
    "year_of_age",
]


def year_of_age(dob: dt.date, age: int) -> int:
    """The calendar year in which someone born on dob turns the given age."""
    return dob.year + age


def build_timeline(dob: dt.date, occupation: str,
                   rng: Optional[random.Random] = None,
                   today: Optional[dt.date] = None) -> List[Dict]:
    """Build a chronological life timeline anchored to a date of birth.

    Args:
        dob: The cover's date of birth.
        occupation: The present occupation, used for the final event.
        rng: Seeded RNG for determinism.
        today: Reference date; defaults to the real today.

    Returns:
        A list of {year, age, event, detail} dicts, sorted by year.
    """
    rng = rng or random.Random()
    today = today or dt.date.today()
    current_age = today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day))

    events: List[Dict] = []

    def add(age: int, event: str, detail: str) -> None:
        if age < 0 or age > current_age:
            return  # skip events that would land in the future or before birth
        events.append({
            "year": year_of_age(dob, age),
            "age": age,
            "event": event,
            "detail": detail,
        })

    add(0, "born", f"Born in {corpus.pick(rng, ['a coastal town', 'a railway city', 'a market village'])}.")

    school = corpus.pick(rng, corpus.SCHOOLS)
    add(5 + rng.randrange(2), "school", f"Started at {school}.")

    add(11 + rng.randrange(2), "move",
        f"Family moved; changed schools to {corpus.pick(rng, corpus.SCHOOLS)}.")

    first_job_age = 16 + rng.randrange(4)
    employer = corpus.pick(rng, corpus.EMPLOYERS)
    add(first_job_age, "first job", f"First paid work at {employer}.")

    if current_age >= 21:
        add(19 + rng.randrange(4), "training",
            f"Trained toward {occupation}; picked up {corpus.pick(rng, corpus.SKILLS)}.")

    if current_age >= 26:
        add(24 + rng.randrange(5), "relocation",
            f"Moved for work; settled near {corpus.pick(rng, corpus.SHOPS)}.")

    add(current_age, "present", f"Currently working as {occupation}.")

    events.sort(key=lambda e: e["year"])
    return events


def timeline_to_text(timeline: List[Dict]) -> str:
    """Render a timeline as a readable, dated list."""
    lines = []
    for event in timeline:
        lines.append(f"{event['year']} (age {event['age']}) — "
                     f"{event['event']}: {event['detail']}")
    return "\n".join(lines)


def gap_report(timeline: List[Dict], max_gap: int = 8) -> List[Dict]:
    """Find unexplained gaps between consecutive timeline events.

    A cover's story should not have long silent stretches; a handler can
    use this to decide where to add filler events. Returns a list of
    {from_year, to_year, years} dicts for every gap longer than max_gap.
    """
    gaps: List[Dict] = []
    for prev, nxt in zip(timeline, timeline[1:]):
        span = nxt["year"] - prev["year"]
        if span > max_gap:
            gaps.append({
                "from_year": prev["year"],
                "to_year": nxt["year"],
                "years": span,
            })
    return gaps
