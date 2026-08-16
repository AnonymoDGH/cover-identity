"""Multi-format export for cover-identity dossiers.

Different moments call for different artifacts: a machine-readable JSON
for storage, a markdown dossier for the handler's binder, a one-page
cheat sheet for the operator's pocket, and a redacted version that can be
shown to a third party without giving the whole legend away.

This module takes the dossier dict produced by dossier.assemble() and
renders each of those formats. Every exporter is pure and deterministic,
so the same dossier always produces byte-identical output -- which makes
the exports themselves testable.
"""

from __future__ import annotations

import json
from typing import Dict, List

from . import dossier as _dossier

__all__ = [
    "ExportError",
    "to_json",
    "to_markdown",
    "to_cheat_sheet",
    "to_redacted",
    "EXPORT_FORMATS",
    "export",
]


class ExportError(ValueError):
    """Raised for unknown export formats or malformed dossiers."""


def _require(dossier: Dict, key: str):
    if key not in dossier:
        raise ExportError(f"dossier is missing required key {key!r}")
    return dossier[key]


def to_json(dossier: Dict, indent: int = 2) -> str:
    """Serialize the dossier to JSON.

    Dataclass-based fields (medical, residence, vehicle, etc.) are
    converted via their __dict__ so the output is always serializable.
    """
    _require(dossier, "identity")

    def default(obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"not serializable: {type(obj)!r}")

    return json.dumps(dossier, indent=indent, ensure_ascii=False,
                      default=default, sort_keys=True)


def to_markdown(dossier: Dict) -> str:
    """Render the dossier as a markdown document for the handler's binder."""
    ident = _require(dossier, "identity")
    lines = [
        f"# Cover Dossier — {ident['name']}",
        "",
        "## Basics",
        "",
        f"| Field | Value |",
        f"| --- | --- |",
        f"| Name | {ident['name']} |",
        f"| Age | {ident['age']} (born {ident['date_of_birth']}) |",
        f"| Address | {ident['address']} |",
        f"| Phone | {ident['phone']} |",
        f"| Email | {ident['email']} |",
        f"| Occupation | {ident['occupation']} at {ident['employer']} |",
        "",
        "## Backstory",
        "",
        ident["backstory"],
        "",
        "## Memory Anchors",
        "",
    ]
    for item in dossier.get("drill", []):
        if item["category"] == "anchor":
            lines.append(f"- **{item['prompt']}**: {item['answer']}")
    lines += ["", "## Risk", ""]
    report = dossier.get("risk", {})
    lines.append(f"Overall: **{report.get('band')}** "
                 f"(score {report.get('total')})")
    lines.append("")
    return "\n".join(lines)


def to_cheat_sheet(dossier: Dict) -> str:
    """A one-page pocket card: only what the operator must recite.

    Name, DOB, occupation, address, anchors, and the duress codes --
    nothing more. If it is not on the card, the operator is not expected
    to produce it under pressure.
    """
    ident = _require(dossier, "identity")
    lines = [
        "CHEAT SHEET (memorize, then destroy)",
        "=" * 40,
        f"NAME: {ident['name']}",
        f"DOB:  {ident['date_of_birth']}",
        f"JOB:  {ident['occupation']} @ {ident['employer']}",
        f"HOME: {ident['address']}",
        "",
        "ANCHORS:",
    ]
    for item in dossier.get("drill", []):
        if item["category"] == "anchor":
            lines.append(f"  {item['prompt']}: {item['answer']}")
    lines.append("")
    lines.append("DURESS:")
    for code in dossier.get("duress_codes", []):
        lines.append(f"  '{code.phrase}' -> {code.meaning}")
    return "\n".join(lines)


#: Fields stripped from a redacted export.
_REDACT_FIELDS = ("anchors", "cover_questions", "timeline")


def to_redacted(dossier: Dict) -> Dict:
    """A copy of the dossier safe to show a third party.

    Removes the memory anchors, cover questions, and timeline -- the
    fields that only the operator should know -- and replaces them with
    placeholders. The identity basics stay, because those are the point of
    a redacted legend.
    """
    ident = dict(_require(dossier, "identity"))
    for field in _REDACT_FIELDS:
        if field in ident:
            ident[field] = "[redacted]"
    return {
        "identity": ident,
        "persona": dossier.get("persona"),
        "note": "redacted for third-party viewing",
    }


EXPORT_FORMATS = ("json", "markdown", "cheat-sheet", "redacted")


def export(dossier: Dict, fmt: str) -> str:
    """Dispatch to the right exporter by format name.

    The redacted format is re-serialized to JSON so every format returns
    a string.
    """
    if fmt == "json":
        return to_json(dossier)
    if fmt == "markdown":
        return to_markdown(dossier)
    if fmt == "cheat-sheet":
        return to_cheat_sheet(dossier)
    if fmt == "redacted":
        return json.dumps(to_redacted(dossier), indent=2, ensure_ascii=False,
                          sort_keys=True)
    raise ExportError(f"unknown format {fmt!r}; choose from {EXPORT_FORMATS}")
