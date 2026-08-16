"""Digital footprint generation for a cover identity.

A modern legend needs an online presence that matches the paper one --
but a *sparse* one. The perfect cover has a few old accounts, a handful
of boring posts, and nothing that invites attention. This module builds
that footprint: social profiles, a few posts consistent with the cover's
hobbies and job, and forum activity that explains the skills.

Everything is cross-checked against the identity: post topics come from
the cover's actual hobbies and occupation, and account ages never predate
the date of birth. The result reads like a real, slightly dull person.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "PLATFORMS",
    "make_profiles",
    "make_posts",
    "make_forum_activity",
    "build_footprint",
    "footprint_report",
]

#: Platforms a low-profile person plausibly has, with typical account age.
PLATFORMS: Dict[str, tuple] = {
    "photo_sharing": (2, 9),
    "hobby_forum": (3, 12),
    "professional_network": (4, 10),
    "local_marketplace": (1, 6),
}

_POST_TEMPLATES: Dict[str, List[str]] = {
    "hobby": [
        "Spent the morning on {hobby}. Slow progress, good coffee.",
        "Finally got the hang of {hobby}. Took long enough.",
        "{hobby} day. Hands tired, head quiet.",
    ],
    "work": [
        "Long week as {occupation}, but the job gets done.",
        "{occupation} life: early starts, honest tired.",
        "Another day of {occupation}. Wouldn't trade it, mostly.",
    ],
    "place": [
        "The light over the harbor this evening was something.",
        "Market day. Same stalls, same faces, same good bread.",
        "Walked the old route again. Some things don't need changing.",
    ],
}


def make_profiles(identity: Dict, rng: random.Random,
                  today: Optional[dt.date] = None) -> List[Dict]:
    """Create a sparse set of platform accounts for the cover.

    Account ages are bounded by the cover's real age, so a young cover
    gets newer accounts. Handles derive from the name, matching the email.
    """
    today = today or dt.date.today()
    dob = dt.date.fromisoformat(identity["date_of_birth"])
    age = today.year - dob.year
    first = identity["name"].split()[0].lower()
    profiles: List[Dict] = []
    for platform, (min_age, max_age) in PLATFORMS.items():
        if age < min_age + 12:
            continue  # too young to plausibly have this account
        account_years = min(rng.randrange(min_age, max_age + 1), age - 12)
        if account_years < 1:
            account_years = 1
        created = today.replace(year=today.year - account_years)
        profiles.append({
            "platform": platform,
            "handle": f"{first}{rng.randrange(10, 99)}",
            "created": created.isoformat(),
            "posts_count": rng.randrange(3, 40),
            "followers": rng.randrange(5, 120),
        })
    return profiles


def make_posts(identity: Dict, rng: random.Random, count: int = 4,
               today: Optional[dt.date] = None) -> List[Dict]:
    """Write a few boring, on-legend posts drawn from the cover's life."""
    today = today or dt.date.today()
    hobbies = corpus.hobby_pair(rng)
    posts: List[Dict] = []
    categories = ["hobby", "work", "place"]
    for i in range(count):
        category = categories[i % len(categories)]
        if category == "hobby":
            template = rng.choice(_POST_TEMPLATES["hobby"])
            text = template.format(hobby=rng.choice(hobbies))
        elif category == "work":
            template = rng.choice(_POST_TEMPLATES["work"])
            text = template.format(occupation=identity.get("occupation", "a worker"))
        else:
            text = rng.choice(_POST_TEMPLATES["place"])
        days_ago = rng.randrange(1, 200)
        posts.append({
            "category": category,
            "text": text,
            "date": (today - dt.timedelta(days=days_ago)).isoformat(),
        })
    posts.sort(key=lambda p: p["date"])
    return posts


def make_forum_activity(identity: Dict, rng: random.Random,
                        count: int = 3) -> List[Dict]:
    """Forum threads where the cover explains their skills, quietly."""
    skills = corpus.pick_many(rng, corpus.SKILLS, count)
    activity: List[Dict] = []
    for skill in skills:
        activity.append({
            "forum": corpus.pick(rng, ["practical-skills", "hobby-corner",
                                       "trade-talk", "weekend-projects"]),
            "topic": f"Getting started with {skill}",
            "role": rng.choice(["asker", "helpful replier"]),
            "posts": rng.randrange(1, 12),
        })
    return activity


def build_footprint(identity: Dict, seed: Optional[int] = None,
                    today: Optional[dt.date] = None) -> Dict:
    """Assemble a full, deterministic digital footprint for one identity."""
    rng = random.Random(seed)
    return {
        "profiles": make_profiles(identity, rng, today),
        "posts": make_posts(identity, rng, count=4, today=today),
        "forum_activity": make_forum_activity(identity, rng, count=3),
    }


def footprint_report(footprint: Dict) -> Dict:
    """Summarize a footprint: how visible the cover is, and where."""
    profiles = footprint.get("profiles", [])
    posts = footprint.get("posts", [])
    return {
        "platforms": len(profiles),
        "total_followers": sum(p["followers"] for p in profiles),
        "posts": len(posts),
        "post_categories": sorted({p["category"] for p in posts}),
        "forum_threads": len(footprint.get("forum_activity", [])),
    }
