"""Cover Identity Generator — fictional legends that hold together.

Generates a plausible, internally consistent cover identity: name, date of
birth, address, contact details, occupation, backstory and memory anchors —
the details that make a lie feel lived-in. Deterministic when seeded.

Requires Faker.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
from pathlib import Path

from faker import Faker

from . import corpus, timeline as _timeline

OCCUPATIONS = [
    "freelance translator", "logistics coordinator", "import/export clerk",
    "field service technician", "vintage bookseller", "travel photographer",
    "marina manager", "IT auditor", "catering consultant", "marine surveyor",
]

SKILLS = [
    "sailing", "accounting", "photography", "typing at 110 wpm",
    "locksmithing", "radio repair", "fencing", "piano", "scuba diving",
    "coffee roasting",
]

BACKSTORY = (
    "Born in {birth_city} in {birth_year}, {first} grew up above {parents_shop}. "
    "The family relocated to {moved_city} when {first} was twelve, after "
    "{parents_shop} burned down in a suspicious fire. Since then, {first} "
    "has worked as {occupation}. Colleagues at {company} know {first} as "
    "quiet, reliable, and oddly good with locks. Nobody asks about the old "
    "name. Nobody has to."
)

ANCHOR_QUESTIONS = [
    ("mother's maiden name", "mother_maiden"),
    ("childhood pet", "childhood_pet"),
    ("street you grew up on", "home_street"),
    ("first school", "first_school"),
    ("license plate", "license_plate"),
]


def _age_from_dob(dob: dt.date, today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _make_dob(rng: random.Random, today: dt.date,
              minimum_age: int = 28, maximum_age: int = 55) -> dt.date:
    """A deterministic date of birth anchored to the reference date.

    Faker's own date_of_birth always uses the real today, which breaks
    consistency when a caller injects a reference date. So we draw the age
    and the in-year offset from the seeded RNG instead.
    """
    age = rng.randint(minimum_age, maximum_age)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)  # safe for every month
    birth_year = today.year - age
    dob = dt.date(birth_year, month, day)
    # If the birthday has not happened yet this year, the person is age-1
    # until it does; nudge the year so the stated age matches exactly.
    if (today.month, today.day) < (month, day):
        dob = dt.date(birth_year + 1, month, day)
    return dob


def generate(locale: str = "en_US", seed: int | None = None,
             template: str = "agent",
             today: dt.date | None = None) -> dict:
    """Build a cover identity dict. Same seed → same identity.

    Args:
        locale: Faker locale.
        seed: Deterministic seed.
        template: Reserved for future archetype templates.
        today: Reference date for age/DOB/timeline; defaults to the real
            today. Injecting it keeps the whole identity internally
            consistent and reproducible.
    """
    fake = Faker(locale)
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
    today = today or dt.date.today()

    dob = _make_dob(random.Random(seed if seed is not None else random.random()),
                    today)
    age = _age_from_dob(dob, today)
    full = fake.name().strip()
    parts = full.split()
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else fake.last_name()
    email_local = re.sub(r"[^a-z0-9]", "", (first + last).lower())
    email = f"{email_local}@{fake.free_email_domain()}"

    anchors = {
        "mother_maiden": fake.last_name(),
        "childhood_pet": fake.first_name(),
        "home_street": fake.street_name(),
        "first_school": f"{fake.city()} Elementary",
        "license_plate": fake.license_plate(),
    }

    company = f"{fake.company()}"
    occupation = corpus.occupation_for_age(random.Random(seed if seed is not None
                                                       else random.random()), age)
    backstory = BACKSTORY.format(
        birth_city=fake.city(),
        birth_year=str(dob.year),
        first=first,
        parents_shop=fake.company(),
        moved_city=fake.city(),
        occupation=occupation,
        company=company,
    )

    life = _timeline.build_timeline(dob, occupation,
                                    rng=random.Random(seed if seed is not None
                                                      else random.random()),
                                    today=today)

    return {
        "name": full,
        "age": age,
        "date_of_birth": dob.isoformat(),
        "address": fake.address().replace("\n", ", "),
        "phone": fake.phone_number(),
        "email": email,
        "occupation": occupation,
        "employer": company,
        "backstory": backstory,
        "timeline": life,
        "anchors": anchors,
        "cover_questions": [
            {"question": q, "answer": anchors[k]}
            for q, k in ANCHOR_QUESTIONS
        ],
    }


def export_json(identity: dict) -> str:
    return json.dumps(identity, indent=2, ensure_ascii=False)


def export_markdown(identity: dict) -> str:
    lines = [
        "# Cover Identity",
        "",
        f"**Name:** {identity['name']}",
        f"**Age:** {identity['age']} (born {identity['date_of_birth']})",
        f"**Address:** {identity['address']}",
        f"**Phone:** {identity['phone']}",
        f"**Email:** {identity['email']}",
        f"**Occupation:** {identity['occupation']} at {identity['employer']}",
        "",
        "## Backstory",
        "",
        identity["backstory"],
        "",
        "## Memory anchors",
        "",
    ]
    for q, a in identity["cover_questions"]:
        lines.append(f"- {q}: {a}")
    return "\n".join(lines)


def quiz(identity: dict) -> list[dict]:
    """Questions for the memorize drill — one per anchor, plus the basics."""
    return [
        {"q": "Full name", "a": identity["name"]},
        {"q": "Date of birth", "a": identity["date_of_birth"]},
        {"q": "Occupation", "a": identity["occupation"]},
    ] + [
        {"q": f"Your {item['question']}", "a": item["answer"]}
        for item in identity["cover_questions"]
    ]


__all__ = ["OCCUPATIONS", "generate", "export_json", "export_markdown", "quiz"]
