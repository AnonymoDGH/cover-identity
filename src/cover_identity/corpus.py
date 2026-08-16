"""Embedded data corpus for cover identities.

Everything a legend needs to feel lived-in, stored as plain Python data so
the package works offline and deterministically. Faker supplies the
surface details (names, addresses); this module supplies the *texture* --
the occupations, hobbies, habits, shops, and backstory fragments that make
a cover hold up under casual conversation.

The data is deliberately mundane. A good cover is boring: nobody
remembers the person who roasts coffee and fixes radios.
"""

from __future__ import annotations

import random
from typing import Dict, List, Sequence, Tuple

__all__ = [
    "OCCUPATIONS",
    "SKILLS",
    "HOBBIES",
    "HABITS",
    "PERSONALITY_TRAITS",
    "SHOPS",
    "VEHICLES",
    "PETS",
    "SCHOOLS",
    "EMPLOYERS",
    "BACKSTORY_BEATS",
    "ANCHOR_QUESTIONS",
    "QUIP_LINES",
    "pick",
    "pick_many",
    "occupation_for_age",
    "hobby_pair",
]

# ---------------------------------------------------------------------------
# Occupations, grouped by sector so a timeline can stay coherent.
# ---------------------------------------------------------------------------

OCCUPATIONS: Dict[str, List[str]] = {
    "trades": [
        "field service technician", "locksmith", "marine surveyor",
        "radio repair technician", "electrician", "HVAC mechanic",
        "boatyard rigger", "watch repairer",
    ],
    "logistics": [
        "logistics coordinator", "import/export clerk", "freight dispatcher",
        "warehouse supervisor", "customs broker", "fleet scheduler",
    ],
    "knowledge": [
        "freelance translator", "IT auditor", "technical writer",
        "archivist", "cartographer", "grant researcher",
    ],
    "hospitality": [
        "marina manager", "catering consultant", "hotel night auditor",
        "tour guide", "barista trainer", "event steward",
    ],
    "creative": [
        "travel photographer", "vintage bookseller", "letterpress printer",
        "documentary editor", "sign painter",
    ],
}

#: Flat list kept for backward compatibility with the original API.
FLAT_OCCUPATIONS: List[str] = [o for group in OCCUPATIONS.values() for o in group]

SKILLS: List[str] = [
    "sailing", "accounting", "photography", "typing at 110 wpm",
    "locksmithing", "radio repair", "fencing", "piano", "scuba diving",
    "coffee roasting", "bookbinding", "knot tying", "map reading",
    "small-engine repair", "first aid", "sign language", "chess",
    "woodworking", "bird identification", "shortwave listening",
]

HOBBIES: List[str] = [
    "restoring old cameras", "urban sketching", "sourdough baking",
    "long-distance cycling", "collecting nautical charts", "amateur radio",
    "trail running", "fermenting hot sauce", "model shipbuilding",
    "birdwatching", "flea-market hunting", "learning dead languages",
    "sea glass collecting", "hand-drip coffee", "bouldering",
]

HABITS: List[str] = [
    "reads the shipping forecast before bed", "always pays in cash",
    "keeps a paper notebook, never a phone", "takes the same route to work",
    "arrives ten minutes early to everything", "never drinks alcohol on weekdays",
    "writes letters instead of emails", "checks the exits in every room",
    "buys the same newspaper every morning", "keeps a go-bag by the door",
]

PERSONALITY_TRAITS: List[str] = [
    "quiet", "reliable", "methodical", "unflappable", "soft-spoken",
    "dry-humored", "observant", "patient", "tidy", "self-contained",
    "courteous", "hard to read",
]

SHOPS: List[str] = [
    "a hardware store", "a secondhand bookshop", "a chandlery",
    "a family bakery", "a print shop", "a marine supply store",
    "a camera repair shop", "a spice merchant", "a locksmith's kiosk",
    "an art-supply house",
]

VEHICLES: List[str] = [
    "a dented panel van", "a well-kept bicycle", "a secondhand sedan",
    "a small sailboat", "a motorbike", "a battered pickup",
    "no vehicle, by choice",
]

PETS: List[str] = [
    "a one-eyed tabby cat", "an elderly labrador", "a rescue greyhound",
    "a talkative parrot", "two pond turtles", "no pet, but feeds the strays",
]

SCHOOLS: List[str] = [
    "a small coastal primary", "a railway-town comprehensive",
    "a monastery school", "a maritime academy", "a forest-school program",
    "an evening technical college",
]

EMPLOYERS: List[str] = [
    "a regional freight line", "a municipal archive", "a marina co-op",
    "a translation bureau", "a heritage trust", "a catering collective",
    "a survey firm", "a print works",
]

# ---------------------------------------------------------------------------
# Backstory beats: composable sentence fragments.
# ---------------------------------------------------------------------------

BACKSTORY_BEATS: Dict[str, List[str]] = {
    "origin": [
        "Born in {birth_city} in {birth_year}, {first} grew up above {shop}.",
        "{first} was born in {birth_city} in {birth_year}, the second of three children.",
        "The family kept a {shop} in {birth_city}, where {first} was born in {birth_year}.",
    ],
    "disruption": [
        "The family relocated to {moved_city} when {first} was twelve, after {shop} burned down in a suspicious fire.",
        "A flood took the family home when {first} was nine, and they started over in {moved_city}.",
        "When the {shop} closed, the family moved to {moved_city} for work.",
    ],
    "trade": [
        "Since then, {first} has worked as {occupation}.",
        "{first} fell into the trade early and has been {occupation} ever since.",
        "These days {first} keeps busy as {occupation}.",
    ],
    "reputation": [
        "Colleagues at {company} know {first} as {trait}, {trait2}, and oddly good with locks.",
        "Around {company}, {first} has a reputation for being {trait} and {trait2}.",
        "People at {company} describe {first} as {trait}, though {trait2} when pressed.",
    ],
    "closer": [
        "Nobody asks about the old name. Nobody has to.",
        "The past stays folded, like a chart you only open at sea.",
        "Some doors stay shut, and {first} keeps the key.",
    ],
}

ANCHOR_QUESTIONS: List[Tuple[str, str]] = [
    ("mother's maiden name", "mother_maiden"),
    ("childhood pet", "childhood_pet"),
    ("street you grew up on", "home_street"),
    ("first school", "first_school"),
    ("license plate", "license_plate"),
    ("name of your first boss", "first_boss"),
    ("town of your first job", "first_job_town"),
]

QUIP_LINES: List[str] = [
    "I keep to myself, mostly.",
    "Long hours, early starts -- you know how it is.",
    "I'm terrible with gossip, sorry.",
    "That's a story for another time.",
    "I just fix things. People remember that.",
]


def pick(rng: random.Random, options: Sequence[str]) -> str:
    """Choose one option with the given RNG (deterministic under a seed)."""
    return rng.choice(list(options))


def pick_many(rng: random.Random, options: Sequence[str], n: int) -> List[str]:
    """Choose n distinct options, preserving a stable order by index."""
    pool = list(options)
    if n > len(pool):
        n = len(pool)
    chosen = rng.sample(pool, n)
    # Return in original order so output is stable for a given sample.
    order = {v: i for i, v in enumerate(pool)}
    return sorted(chosen, key=lambda v: order[v])


def occupation_for_age(rng: random.Random, age: int) -> str:
    """Pick an occupation plausible for the given age.

    Younger covers skew to logistics/hospitality; older ones to
    trades/knowledge where a long history reads naturally.
    """
    if age < 32:
        sector = pick(rng, ["logistics", "hospitality", "creative"])
    elif age < 45:
        sector = pick(rng, ["trades", "logistics", "knowledge", "creative"])
    else:
        sector = pick(rng, ["trades", "knowledge", "hospitality"])
    return pick(rng, OCCUPATIONS[sector])


def hobby_pair(rng: random.Random) -> Tuple[str, str]:
    """Two distinct hobbies that read well together."""
    a, b = pick_many(rng, HOBBIES, 2)
    return a, b
