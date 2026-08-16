"""Consistency checking for cover identities.

A legend falls apart on the small contradictions: an age that does not
match the date of birth, an email that does not match the name, a job
history that starts before the person was born. This module audits an
identity dict and returns a list of findings, each with a severity.

It is deliberately tolerant of style and strict about arithmetic. The
goal is to catch the mistakes a tired handler makes at 2 a.m., not to
judge the quality of the prose.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

__all__ = [
    "Severity",
    "Finding",
    "check_age_dob",
    "check_email_name",
    "check_phone_shape",
    "check_backstory_names",
    "check_anchors_present",
    "check_timeline",
    "audit",
]


class Severity:
    """Finding severity levels, ordered from least to most serious."""

    INFO = "info"
    WARN = "warn"
    ERROR = "error"

    ORDER = {INFO: 0, WARN: 1, ERROR: 2}


@dataclass(frozen=True)
class Finding:
    """One consistency problem found in an identity."""

    field: str
    severity: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


def _age_from_dob(dob: dt.date, today: Optional[dt.date] = None) -> int:
    today = today or dt.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def check_age_dob(identity: Dict, today: Optional[dt.date] = None) -> List[Finding]:
    """Verify the stated age matches the date of birth."""
    findings: List[Finding] = []
    dob_raw = identity.get("date_of_birth")
    age = identity.get("age")
    if not dob_raw:
        findings.append(Finding("date_of_birth", Severity.ERROR, "missing"))
        return findings
    try:
        dob = dt.date.fromisoformat(str(dob_raw))
    except ValueError:
        findings.append(Finding("date_of_birth", Severity.ERROR,
                                f"unparseable date {dob_raw!r}"))
        return findings
    if age is None:
        findings.append(Finding("age", Severity.WARN, "age not stated"))
        return findings
    expected = _age_from_dob(dob, today)
    if int(age) != expected:
        findings.append(Finding("age", Severity.ERROR,
                                f"stated {age} but DOB implies {expected}"))
    return findings


def check_email_name(identity: Dict) -> List[Finding]:
    """Verify the email local part plausibly derives from the name."""
    findings: List[Finding] = []
    email = identity.get("email", "")
    name = identity.get("name", "")
    if "@" not in email:
        findings.append(Finding("email", Severity.ERROR, "not an email address"))
        return findings
    local = email.split("@", 1)[0].lower()
    if not name:
        findings.append(Finding("email", Severity.WARN,
                                "cannot verify against an empty name"))
        return findings
    first = name.split()[0].lower()
    # The local part should at least start with the first name's letters.
    if not local.startswith(first[:2]):
        findings.append(Finding("email", Severity.WARN,
                                f"local part {local!r} does not echo name {name!r}"))
    return findings


def check_phone_shape(identity: Dict) -> List[Finding]:
    """Verify the phone number has a plausible digit count."""
    findings: List[Finding] = []
    phone = identity.get("phone", "")
    digits = re.sub(r"\D", "", phone)
    if not (7 <= len(digits) <= 15):
        findings.append(Finding("phone", Severity.WARN,
                                f"{len(digits)} digits is implausible"))
    return findings


def check_backstory_names(identity: Dict) -> List[Finding]:
    """Verify the backstory mentions the cover's own first name."""
    findings: List[Finding] = []
    backstory = identity.get("backstory", "")
    name = identity.get("name", "")
    if not backstory:
        findings.append(Finding("backstory", Severity.WARN, "no backstory"))
        return findings
    if name:
        first = name.split()[0]
        if first not in backstory:
            findings.append(Finding("backstory", Severity.WARN,
                                    f"never mentions the first name {first!r}"))
    return findings


def check_anchors_present(identity: Dict) -> List[Finding]:
    """Verify every cover question has a non-empty answer."""
    findings: List[Finding] = []
    questions = identity.get("cover_questions", [])
    if not questions:
        findings.append(Finding("cover_questions", Severity.WARN,
                                "no memory anchors defined"))
        return findings
    for item in questions:
        answer = str(item.get("answer", "")).strip()
        if not answer:
            findings.append(Finding("cover_questions", Severity.ERROR,
                                    f"empty answer for {item.get('question')!r}"))
    return findings


def check_timeline(identity: Dict, today: Optional[dt.date] = None) -> List[Finding]:
    """Verify any dated life events fall after birth and before today."""
    findings: List[Finding] = []
    timeline = identity.get("timeline")
    if not timeline:
        return findings  # timeline is optional
    dob_raw = identity.get("date_of_birth")
    try:
        dob = dt.date.fromisoformat(str(dob_raw))
    except (ValueError, TypeError):
        return findings  # cannot check without a DOB
    today = today or dt.date.today()
    prev_year: Optional[int] = None
    for event in timeline:
        year = event.get("year")
        if year is None:
            continue
        if year < dob.year:
            findings.append(Finding("timeline", Severity.ERROR,
                                    f"event in {year} predates birth year {dob.year}"))
        if year > today.year:
            findings.append(Finding("timeline", Severity.ERROR,
                                    f"event in {year} is in the future"))
        if prev_year is not None and year < prev_year:
            findings.append(Finding("timeline", Severity.WARN,
                                    f"event in {year} breaks chronological order"))
        prev_year = year
    return findings


def audit(identity: Dict, today: Optional[dt.date] = None) -> List[Finding]:
    """Run every consistency check and return all findings.

    An empty list means the identity is internally consistent.
    """
    findings: List[Finding] = []
    findings += check_age_dob(identity, today)
    findings += check_email_name(identity)
    findings += check_phone_shape(identity)
    findings += check_backstory_names(identity)
    findings += check_anchors_present(identity)
    findings += check_timeline(identity, today)
    return findings


def worst_severity(findings: Sequence[Finding]) -> Optional[str]:
    """Return the most severe level present, or None if clean."""
    if not findings:
        return None
    return max(findings, key=lambda f: Severity.ORDER[f.severity]).severity
