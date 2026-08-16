"""Alias graph for managing multiple cover identities.

A serious operator may hold several legends, each for a different context.
The danger is cross-contamination: using one alias's phone number while
living another, or letting two aliases share an address. This module keeps
a graph of aliases and checks them against each other for exactly that.

Each alias is a lightweight record (name, context, and the identity fields
that matter for collision checks). The graph can add, retire, and list
aliases, and cross_check() reports any field that two active aliases
share -- a shared value is a thread an investigator can pull.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

__all__ = [
    "AliasError",
    "Alias",
    "AliasGraph",
    "from_identity",
]

#: Identity fields that must not collide between active aliases.
_COLLISION_FIELDS = ("address", "phone", "email", "employer")


class AliasError(ValueError):
    """Raised for alias-graph usage problems."""


@dataclass
class Alias:
    """One alias: a name, a context, and the fields that can collide."""

    name: str
    context: str
    active: bool = True
    fields: Dict[str, str] = field(default_factory=dict)

    def value(self, key: str) -> Optional[str]:
        return self.fields.get(key)


class AliasGraph:
    """A collection of aliases with cross-contamination checking."""

    def __init__(self) -> None:
        self._aliases: Dict[str, Alias] = {}

    def add(self, alias: Alias) -> None:
        """Add an alias. Names are unique within the graph."""
        key = alias.name.strip()
        if not key:
            raise AliasError("alias name must not be empty")
        if key in self._aliases:
            raise AliasError(f"alias {key!r} already exists")
        alias.name = key
        self._aliases[key] = alias

    def get(self, name: str) -> Alias:
        if name not in self._aliases:
            raise AliasError(f"no alias named {name!r}")
        return self._aliases[name]

    def retire(self, name: str) -> None:
        """Mark an alias inactive (it stays in the graph for the record)."""
        self.get(name).active = False

    def names(self, active_only: bool = False) -> List[str]:
        """Alias names, sorted; optionally only the active ones."""
        result = [a.name for a in self._aliases.values()
                  if a.active or not active_only]
        return sorted(result)

    def __len__(self) -> int:
        return len(self._aliases)

    def cross_check(self) -> List[Dict]:
        """Find fields shared between two active aliases.

        Returns a list of {field, value, aliases} dicts, one per shared
        value. An empty list means the active aliases are cleanly
        separated.
        """
        active = [a for a in self._aliases.values() if a.active]
        collisions: List[Dict] = []
        for key in _COLLISION_FIELDS:
            seen: Dict[str, List[str]] = {}
            for alias in active:
                value = alias.value(key)
                if value:
                    seen.setdefault(value, []).append(alias.name)
            for value, names in seen.items():
                if len(names) > 1:
                    collisions.append({
                        "field": key,
                        "value": value,
                        "aliases": sorted(names),
                    })
        return collisions

    def separation_report(self) -> Dict:
        """Summarize how well the active aliases are separated."""
        collisions = self.cross_check()
        active = [a for a in self._aliases.values() if a.active]
        return {
            "active_aliases": len(active),
            "retired_aliases": len(self._aliases) - len(active),
            "collisions": len(collisions),
            "clean": not collisions,
            "details": collisions,
        }


def from_identity(name: str, context: str, identity: Dict,
                  active: bool = True) -> Alias:
    """Build an Alias record from a full identity dict.

    Pulls only the collision-relevant fields so the alias stays light.
    """
    return Alias(
        name=name,
        context=context,
        active=active,
        fields={key: str(identity.get(key, "")) for key in _COLLISION_FIELDS},
    )
