"""Medical history layer for a cover identity.

Sooner or later someone asks about allergies, or a form demands a blood
type, or a colleague notices a limp. A legend without a medical story
improvises one under pressure, and improvised medicine is full of holes.
This module builds a small, internally consistent medical layer: a blood
type, a couple of allergies, a long-ago injury that explains a physical
habit, a named doctor, and a vaccination note.

The design rule is *boring and common*. Rare conditions invite follow-up
questions and records checks. Common ones close the conversation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "MedicalError",
    "BLOOD_TYPES",
    "MedicalProfile",
    "build_medical_profile",
    "medical_card",
]


class MedicalError(ValueError):
    """Raised for medical-layer usage problems."""


#: Common blood types, weighted toward the frequent ones.
BLOOD_TYPES: List[str] = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]

_ALLERGIES: List[str] = [
    "penicillin", "hay fever (seasonal)", "mild lactose intolerance",
    "bee stings", "shellfish", "none known",
]
_OLD_INJURIES: List[str] = [
    "a broken wrist from a cycling fall, healed fine",
    "a twisted ankle that aches in cold weather",
    "a cracked rib from old sports, long since healed",
    "no significant old injuries",
]
_CONDITIONS: List[str] = [
    "mild asthma, rarely needs the inhaler",
    "occasional migraines, managed with rest",
    "no chronic conditions",
    "no chronic conditions",
]


@dataclass
class MedicalProfile:
    """A boring, consistent medical story."""

    blood_type: str
    allergies: List[str]
    old_injury: str
    condition: str
    doctor_name: str
    last_checkup: str

    def summary(self) -> str:
        allergies = ", ".join(self.allergies) if self.allergies else "none known"
        return (f"Blood {self.blood_type}; allergies: {allergies}; "
                f"{self.old_injury}; {self.condition}.")


_DOCTORS = ["Dr. Marsh", "Dr. Okafor", "Dr. Lindqvist", "Dr. Reyes",
            "Dr. Ashby", "Dr. Novak"]


def build_medical_profile(rng: random.Random, age: int,
                          today_year: Optional[int] = None) -> MedicalProfile:
    """A deterministic medical profile scaled to the cover's age."""
    if age < 0:
        raise MedicalError("age must be >= 0")
    today_year = today_year or 2024
    # Weight blood type toward the common ones.
    blood = rng.choices(BLOOD_TYPES, weights=[35, 30, 10, 4, 8, 6, 2, 1])[0]
    # One or two allergies, never zero entries duplicated.
    n_allergies = rng.randrange(1, 3)
    allergies = rng.sample(_ALLERGIES, n_allergies)
    if "none known" in allergies and len(allergies) > 1:
        allergies.remove("none known")
    # Last checkup within the past few years, not in the future.
    years_ago = rng.randrange(0, 4)
    return MedicalProfile(
        blood_type=blood,
        allergies=allergies,
        old_injury=rng.choice(_OLD_INJURIES),
        condition=rng.choice(_CONDITIONS),
        doctor_name=rng.choice(_DOCTORS),
        last_checkup=str(today_year - years_ago),
    )


def medical_card(profile: MedicalProfile, name: str, dob: str) -> str:
    """Render the profile as a wallet-card style text block."""
    return "\n".join([
        "MEDICAL CARD",
        f"  name:        {name}",
        f"  dob:         {dob}",
        f"  blood type:  {profile.blood_type}",
        f"  allergies:   {', '.join(profile.allergies)}",
        f"  history:     {profile.old_injury}",
        f"  condition:   {profile.condition}",
        f"  doctor:      {profile.doctor_name}",
        f"  last visit:  {profile.last_checkup}",
    ])
