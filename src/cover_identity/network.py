"""Social network generation for a cover identity.

Nobody exists alone. A believable cover has a small web of people who
would vouch for them, lend them tools, or nod at the coffee shop. This
module builds that web: a handful of contacts, each with a relationship, a
context for how they know the cover, and a rough closeness score.

The network is deliberately small and low-drama. A cover with thirty
close friends is a cover that will be checked. Five acquaintances and one
good friend is a cover that gets left alone.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "RELATIONSHIPS",
    "make_contact",
    "build_network",
    "vouch_list",
    "network_to_text",
]

#: Relationship types with a typical closeness range (0..1).
RELATIONSHIPS: Dict[str, tuple] = {
    "neighbor": (0.2, 0.5),
    "coworker": (0.3, 0.6),
    "shopkeeper": (0.1, 0.4),
    "old friend": (0.6, 0.9),
    "landlord": (0.2, 0.5),
    "club member": (0.2, 0.6),
    "family friend": (0.4, 0.7),
}

_CONTEXTS: Dict[str, List[str]] = {
    "neighbor": ["lives two doors down", "shares the back alley",
                 "has a dog that escapes into the cover's yard"],
    "coworker": ["works the same shift", "trained the cover on the tools",
                 "splits lunch orders with the cover"],
    "shopkeeper": ["runs the place the cover buys supplies",
                   "keeps the cover's usual order aside"],
    "old friend": ["goes back to the previous town",
                   "knows the cover from before the move"],
    "landlord": ["collects rent on the first of the month",
                 "fixes the boiler when asked, eventually"],
    "club member": ["meets the cover at the hobby club",
                    "lends the cover equipment on weekends"],
    "family friend": ["knew the cover's parents",
                      "sends a card every birthday"],
}


def make_contact(rng: random.Random, relationship: Optional[str] = None) -> Dict:
    """Create one contact with a name, relationship, context, and closeness."""
    rel = relationship or rng.choice(list(RELATIONSHIPS))
    lo, hi = RELATIONSHIPS[rel]
    closeness = round(lo + rng.random() * (hi - lo), 2)
    first = rng.choice(["Mara", "Ivo", "Petra", "Sam", "Nadia", "Owen",
                        "Ruth", "Eli", "Vera", "Tomas", "Ines", "Bram"])
    last = rng.choice(["Keller", "Marsh", "Okafor", "Lindqvist", "Reyes",
                       "Novak", "Ashby", "Ferreira", "Grant", "Molina"])
    return {
        "name": f"{first} {last}",
        "relationship": rel,
        "context": rng.choice(_CONTEXTS[rel]),
        "closeness": closeness,
    }


def build_network(seed: Optional[int] = None, size: int = 5) -> List[Dict]:
    """Build a small, deterministic social network.

    Guarantees at most one "old friend" (the deep contact) and fills the
    rest with lighter ties, so the web reads as real rather than staged.
    """
    rng = random.Random(seed)
    if size < 1:
        raise ValueError("network size must be >= 1")
    contacts: List[Dict] = []
    # One deep tie if there is room.
    if size >= 2:
        contacts.append(make_contact(rng, "old friend"))
    light = [r for r in RELATIONSHIPS if r != "old friend"]
    while len(contacts) < size:
        contacts.append(make_contact(rng, rng.choice(light)))
    return contacts


def vouch_list(network: List[Dict], threshold: float = 0.5) -> List[Dict]:
    """Contacts close enough to vouch for the cover in a pinch."""
    return [c for c in network if c["closeness"] >= threshold]


def network_to_text(network: List[Dict]) -> str:
    """Render the network as a readable list."""
    lines = []
    for c in sorted(network, key=lambda c: -c["closeness"]):
        lines.append(f"- {c['name']} ({c['relationship']}, "
                     f"closeness {c['closeness']:.2f}) — {c['context']}")
    return "\n".join(lines)
