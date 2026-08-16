"""Legend versioning and change log.

A legend is not static: details get patched after a shaky answer, documents
get renewed, addresses change. Every edit is a risk, because the operator
must remember the new version and forget the old one. This module keeps a
versioned change log of a legend so there is always one authoritative
current text and a record of what changed, when, and why.

Each entry records the field, the old value, the new value, and the
reason. The log can produce a "memorize these changes" list for the
operator and a diff-style summary for the handler, and it refuses to
record a change that does not actually change anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "LegendLogError",
    "ChangeEntry",
    "LegendLog",
]


class LegendLogError(ValueError):
    """Raised for legend-log usage problems."""


@dataclass(frozen=True)
class ChangeEntry:
    """One recorded change to a legend field."""

    version: int
    field: str
    old_value: str
    new_value: str
    reason: str


class LegendLog:
    """A versioned change log for one legend."""

    def __init__(self, legend_name: str) -> None:
        if not legend_name.strip():
            raise LegendLogError("legend_name must not be empty")
        self.legend_name = legend_name.strip()
        self._entries: List[ChangeEntry] = []
        self._version = 1

    @property
    def version(self) -> int:
        return self._version

    def change(self, field: str, old_value: str, new_value: str,
               reason: str) -> ChangeEntry:
        """Record a change and bump the version.

        Raises:
            LegendLogError: If the values are identical or the reason is
                empty (a change without a reason is a change nobody can
                defend later).
        """
        if old_value == new_value:
            raise LegendLogError("old and new values are identical")
        if not reason.strip():
            raise LegendLogError("a change needs a reason")
        if not field.strip():
            raise LegendLogError("field must not be empty")
        self._version += 1
        entry = ChangeEntry(version=self._version, field=field.strip(),
                            old_value=old_value, new_value=new_value,
                            reason=reason.strip())
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> List[ChangeEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def fields_changed(self) -> List[str]:
        """Distinct fields that have ever changed, in first-change order."""
        seen: List[str] = []
        for entry in self._entries:
            if entry.field not in seen:
                seen.append(entry.field)
        return seen

    def latest_for(self, field: str) -> Optional[ChangeEntry]:
        """The most recent change to a field, if any."""
        for entry in reversed(self._entries):
            if entry.field == field:
                return entry
        return None

    def memorize_list(self) -> List[str]:
        """The current value of every changed field, for the operator.

        This is the list to drill after a patch: only the things that are
        different now, phrased as the new truth.
        """
        lines: List[str] = []
        for field in self.fields_changed():
            entry = self.latest_for(field)
            lines.append(f"{field}: {entry.new_value}")
        return lines

    def to_text(self) -> str:
        """Render the full change log for the handler's binder."""
        lines = [f"LEGEND LOG: {self.legend_name} (v{self._version})"]
        for entry in self._entries:
            lines.append(f"  v{entry.version} {entry.field}: "
                         f"{entry.old_value!r} -> {entry.new_value!r} "
                         f"({entry.reason})")
        return "\n".join(lines)
