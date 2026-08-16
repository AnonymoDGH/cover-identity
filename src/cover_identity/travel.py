"""Travel history for a cover identity.

A passport tells a story on its own, and that story has to match the
legend. If the cover claims to have lived quietly in one town, a passport
full of exotic stamps is a contradiction. This module builds a travel
history scaled to the persona: a quiet tradesperson gets a couple of
nearby trips; a well-traveled creative gets a longer, wider list.

Every trip is dated after the date of birth and before the reference
date, and the destinations are drawn from a neutral, fictional-friendly
list. The result is a list of trips that an interviewer could ask about
and that the operator can actually answer.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Dict, List, Optional

__all__ = [
    "DESTINATIONS",
    "TRIP_PURPOSES",
    "travel_volume_for",
    "make_trip",
    "build_travel_history",
    "travel_report",
]

#: Neutral destination names (fictional-friendly, no real sensitive states).
DESTINATIONS: List[str] = [
    "the lake district", "the northern coast", "the old capital",
    "the wine country", "the mountain passes", "the harbor city",
    "the border market town", "the island ferry route",
]

TRIP_PURPOSES: List[str] = [
    "visiting family", "a short holiday", "work", "a wedding",
    "a trade fair", "a hiking trip",
]

#: Persona network_shape / loudness -> typical number of trips.
_VOLUME: Dict[str, tuple] = {
    "low": (1, 3),
    "medium": (3, 6),
    "large": (5, 9),
}


def travel_volume_for(loudness: str) -> tuple:
    """The (min, max) trip count for a given footprint loudness."""
    return _VOLUME.get(loudness, (2, 5))


def make_trip(rng: random.Random, dob: dt.date,
              today: Optional[dt.date] = None) -> Dict:
    """One plausible trip, dated between adulthood and the reference date."""
    today = today or dt.date.today()
    earliest = dob + dt.timedelta(days=365 * 18)
    if earliest >= today:
        earliest = today - dt.timedelta(days=365)
    span_days = max(1, (today - earliest).days)
    start = earliest + dt.timedelta(days=rng.randrange(span_days))
    duration = rng.randrange(2, 15)
    return {
        "destination": rng.choice(DESTINATIONS),
        "purpose": rng.choice(TRIP_PURPOSES),
        "start": start.isoformat(),
        "days": duration,
    }


def build_travel_history(identity: Dict, seed: Optional[int] = None,
                         today: Optional[dt.date] = None) -> List[Dict]:
    """Build a deterministic travel history scaled to the persona.

    Reads the persona's footprint_loudness if present; otherwise uses a
    medium volume. Trips are sorted by start date.
    """
    rng = random.Random(seed)
    today = today or dt.date.today()
    dob = dt.date.fromisoformat(identity["date_of_birth"])
    loudness = identity.get("persona", {}).get("footprint_loudness", "medium")
    lo, hi = travel_volume_for(loudness)
    count = rng.randrange(lo, hi + 1)
    trips = [make_trip(rng, dob, today) for _ in range(count)]
    trips.sort(key=lambda t: t["start"])
    return trips


def travel_report(trips: List[Dict]) -> Dict:
    """Summarize a travel history: count, span, and most-visited place."""
    if not trips:
        return {"trips": 0, "destinations": 0, "total_days": 0,
                "most_visited": None}
    counts: Dict[str, int] = {}
    total_days = 0
    for trip in trips:
        counts[trip["destination"]] = counts.get(trip["destination"], 0) + 1
        total_days += trip["days"]
    most_visited = max(counts, key=lambda d: counts[d])
    return {
        "trips": len(trips),
        "destinations": len(counts),
        "total_days": total_days,
        "most_visited": most_visited,
    }
