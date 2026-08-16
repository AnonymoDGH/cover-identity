"""Persona archetypes for cover identities.

Rather than a fully random legend, a handler often wants a *type*: the
quiet tradesperson, the well-traveled creative, the unremarkable clerk.
This module defines named archetypes that bias the generator toward a
coherent character -- a preferred occupation sector, a hobby flavor, a
footprint loudness, and a network shape.

Applying a persona does not replace randomness; it narrows the choices so
the result hangs together. Each persona is a plain dict, so new ones are
easy to add and to serialize.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "PERSONAS",
    "list_personas",
    "get_persona",
    "apply_persona",
    "PersonaError",
]


class PersonaError(ValueError):
    """Raised when an unknown persona is requested."""


#: Named archetypes. Each biases sector, hobbies, footprint, and network.
PERSONAS: Dict[str, Dict] = {
    "tradesperson": {
        "description": "Quiet, skilled, works with their hands. Blends into any worksite.",
        "sector": "trades",
        "hobby_flavor": ["woodworking", "small-engine repair", "knot tying"],
        "footprint_loudness": "low",
        "network_shape": "small",
    },
    "creative": {
        "description": "Well-traveled, a little eccentric, explains odd hours and odd gear.",
        "sector": "creative",
        "hobby_flavor": ["urban sketching", "restoring old cameras", "hand-drip coffee"],
        "footprint_loudness": "medium",
        "network_shape": "medium",
    },
    "clerk": {
        "description": "The most forgettable person in the room. Paperwork is their camouflage.",
        "sector": "logistics",
        "hobby_flavor": ["chess", "birdwatching", "sourdough baking"],
        "footprint_loudness": "low",
        "network_shape": "small",
    },
    "host": {
        "description": "Works hospitality; knows everyone, is remembered by no one in particular.",
        "sector": "hospitality",
        "hobby_flavor": ["fermenting hot sauce", "flea-market hunting", "trail running"],
        "footprint_loudness": "medium",
        "network_shape": "large",
    },
    "scholar": {
        "description": "Archivist or researcher; explains travel, odd questions, and long silences.",
        "sector": "knowledge",
        "hobby_flavor": ["learning dead languages", "collecting nautical charts", "bookbinding"],
        "footprint_loudness": "low",
        "network_shape": "small",
    },
}


def list_personas() -> List[str]:
    """The names of all available personas, sorted."""
    return sorted(PERSONAS)


def get_persona(name: str) -> Dict:
    """Fetch one persona by name.

    Raises:
        PersonaError: If the name is unknown.
    """
    if name not in PERSONAS:
        raise PersonaError(
            f"unknown persona {name!r}; choose from {list_personas()}")
    return PERSONAS[name]


def apply_persona(identity: Dict, name: str,
                  seed: Optional[int] = None) -> Dict:
    """Bias an existing identity toward the named archetype.

    Returns a new identity dict (the input is not mutated) with the
    occupation swapped to the persona's sector, hobbies nudged toward the
    persona's flavor, and footprint/network hints recorded.
    """
    persona = get_persona(name)
    rng = random.Random(seed)
    result = dict(identity)

    # Occupation from the persona's sector.
    result["occupation"] = rng.choice(corpus.OCCUPATIONS[persona["sector"]])

    # Hobbies: keep one random, add one from the persona flavor.
    flavor = persona["hobby_flavor"]
    result["hobbies"] = [
        corpus.pick(rng, corpus.HOBBIES),
        rng.choice(flavor),
    ]

    # Record the persona's operational hints for downstream builders.
    result["persona"] = {
        "name": name,
        "footprint_loudness": persona["footprint_loudness"],
        "network_shape": persona["network_shape"],
        "description": persona["description"],
    }
    return result


def network_size_for(shape: str) -> int:
    """Map a persona's network shape to a concrete contact count."""
    return {"small": 3, "medium": 5, "large": 8}.get(shape, 5)
