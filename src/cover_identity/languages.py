"""Language and accent layer for a cover identity.

A legend that claims to be from one town but swears in another region's
slang is a legend with a hole in it. This module builds the linguistic
layer: the cover's native language, any working languages with honest
proficiency levels, the regional accent to maintain, and a short list of
local phrases the operator should actually be able to use.

Proficiency is graded on a simple four-step scale so it can be drilled
and so the dossier can warn when a claimed skill outruns what the cover
could plausibly defend in conversation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "LanguagesError",
    "PROFICIENCY",
    "LanguageSkill",
    "LanguageProfile",
    "build_language_profile",
    "local_phrases",
    "profile_to_text",
]


class LanguagesError(ValueError):
    """Raised for language-layer usage problems."""


#: Four-step proficiency scale, low to high.
PROFICIENCY: List[str] = ["a few words", "conversational", "fluent", "native"]

_LANGUAGES: List[str] = [
    "the national language", "a neighboring country's tongue",
    "a trade language", "a regional dialect",
]

_ACCENTS: List[str] = [
    "a soft coastal accent", "a clipped city accent",
    "a slow rural drawl", "a neutral educated tone",
]

_PHRASES: List[str] = [
    "a greeting for the shopkeeper",
    "a polite way to decline a drink",
    "a complaint about the weather",
    "a toast at a dinner",
    "a phrase for 'see you tomorrow'",
]


@dataclass(frozen=True)
class LanguageSkill:
    """One language at one proficiency level."""

    language: str
    level: str

    def __post_init__(self) -> None:
        if self.level not in PROFICIENCY:
            raise LanguagesError(f"unknown proficiency {self.level!r}")


@dataclass
class LanguageProfile:
    """The cover's full linguistic story."""

    native: str
    accent: str
    skills: List[LanguageSkill]

    def strongest(self) -> Optional[LanguageSkill]:
        """The highest-proficiency non-native skill, if any."""
        non_native = [s for s in self.skills if s.level != "native"]
        if not non_native:
            return None
        return max(non_native, key=lambda s: PROFICIENCY.index(s.level))


def build_language_profile(rng: random.Random, extra_languages: int = 1) -> LanguageProfile:
    """A deterministic language profile.

    The native language is always present at native proficiency; extra
    languages are added at honest, non-native levels.
    """
    if extra_languages < 0:
        raise LanguagesError("extra_languages must be >= 0")
    native = _LANGUAGES[0]
    skills = [LanguageSkill(language=native, level="native")]
    extras = rng.sample(_LANGUAGES[1:], min(extra_languages, len(_LANGUAGES) - 1))
    for language in extras:
        level = rng.choice(PROFICIENCY[:-1])  # never claim native in an extra
        skills.append(LanguageSkill(language=language, level=level))
    return LanguageProfile(
        native=native,
        accent=rng.choice(_ACCENTS),
        skills=skills,
    )


def local_phrases(rng: random.Random, count: int = 3) -> List[str]:
    """A deterministic set of local phrases the operator should know."""
    if count < 1:
        raise LanguagesError("count must be >= 1")
    return rng.sample(_PHRASES, min(count, len(_PHRASES)))


def profile_to_text(profile: LanguageProfile, phrases: List[str]) -> str:
    """Render the language layer as a readable block."""
    lines = [
        "LANGUAGE PROFILE",
        f"  native: {profile.native}",
        f"  accent: {profile.accent}",
    ]
    for skill in profile.skills:
        lines.append(f"  - {skill.language}: {skill.level}")
    lines.append("  local phrases to know:")
    for phrase in phrases:
        lines.append(f"    * {phrase}")
    return "\n".join(lines)
