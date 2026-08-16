"""Supporting documents for a cover identity.

A legend is only as strong as its paper trail. This module fabricates the
small, boring documents that make an identity feel real: a library card, a
gym membership, a utility bill, a work badge, a handful of receipts. None
of these are real documents and none try to imitate a specific real
issuer -- they are generic props for fiction, roleplay, and testing.

Each document is a dict with a kind, an issue date, and the fields you
would expect. render_text() turns one into a plain-text prop; a full
"wallet" is just a list of them, and wallet_report() summarizes what the
cover is carrying.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "make_library_card",
    "make_gym_membership",
    "make_utility_bill",
    "make_work_badge",
    "make_receipts",
    "build_wallet",
    "render_text",
    "wallet_report",
]


def _issue_date(dob: dt.date, rng: random.Random,
                today: Optional[dt.date] = None) -> dt.date:
    """A plausible recent issue date: within the last few years, after birth."""
    today = today or dt.date.today()
    years_back = rng.randrange(0, 4)
    candidate = today.replace(year=today.year - years_back)
    if candidate <= dob:
        candidate = dob + dt.timedelta(days=365 * 18)
    return candidate


def make_library_card(identity: Dict, rng: random.Random,
                      today: Optional[dt.date] = None) -> Dict:
    """A public-library membership card."""
    dob = dt.date.fromisoformat(identity["date_of_birth"])
    issued = _issue_date(dob, rng, today)
    return {
        "kind": "library_card",
        "holder": identity["name"],
        "member_id": f"LIB-{rng.randrange(100000, 999999)}",
        "branch": f"{corpus.pick(rng, ['Central', 'Harbor', 'Northgate', 'Old Town'])} Branch",
        "issued": issued.isoformat(),
    }


def make_gym_membership(identity: Dict, rng: random.Random,
                        today: Optional[dt.date] = None) -> Dict:
    """A gym membership, tied to one of the cover's hobbies."""
    dob = dt.date.fromisoformat(identity["date_of_birth"])
    issued = _issue_date(dob, rng, today)
    return {
        "kind": "gym_membership",
        "holder": identity["name"],
        "club": corpus.pick(rng, ["Ironworks Gym", "Riverside Fitness",
                                  "Harbor Athletic Club", "Northside Boxing"]),
        "member_id": f"GYM-{rng.randrange(10000, 99999)}",
        "issued": issued.isoformat(),
    }


def make_utility_bill(identity: Dict, rng: random.Random,
                      today: Optional[dt.date] = None) -> Dict:
    """A utility bill addressed to the cover's address."""
    today = today or dt.date.today()
    month = today.replace(day=1) - dt.timedelta(days=rng.randrange(1, 60))
    return {
        "kind": "utility_bill",
        "holder": identity["name"],
        "provider": corpus.pick(rng, ["City Water & Power", "Coastal Energy",
                                      "Metro Gas Co.", "Valley Electric"]),
        "address": identity.get("address", ""),
        "period": month.strftime("%Y-%m"),
        "amount": f"{rng.randrange(30, 180)}.00",
    }


def make_work_badge(identity: Dict, rng: random.Random,
                    today: Optional[dt.date] = None) -> Dict:
    """An employer ID badge matching the cover's stated job."""
    dob = dt.date.fromisoformat(identity["date_of_birth"])
    issued = _issue_date(dob, rng, today)
    return {
        "kind": "work_badge",
        "holder": identity["name"],
        "employer": identity.get("employer", "an unnamed firm"),
        "role": identity.get("occupation", "staff"),
        "badge_id": f"EMP-{rng.randrange(1000, 9999)}",
        "issued": issued.isoformat(),
    }


def make_receipts(identity: Dict, rng: random.Random, count: int = 3,
                  today: Optional[dt.date] = None) -> List[Dict]:
    """A handful of small cash receipts consistent with the cover's habits."""
    today = today or dt.date.today()
    receipts: List[Dict] = []
    for _ in range(count):
        days_ago = rng.randrange(1, 45)
        receipts.append({
            "kind": "receipt",
            "vendor": corpus.pick(rng, corpus.SHOPS),
            "item": corpus.pick(rng, ["coffee", "rope", "notebook", "film",
                                      "spices", "lamp oil", "glue", "string"]),
            "amount": f"{rng.randrange(2, 60)}.{rng.randrange(0, 99):02d}",
            "date": (today - dt.timedelta(days=days_ago)).isoformat(),
        })
    receipts.sort(key=lambda r: r["date"])
    return receipts


def build_wallet(identity: Dict, seed: Optional[int] = None,
                 today: Optional[dt.date] = None) -> List[Dict]:
    """Assemble a full paper trail for one identity.

    Deterministic under a seed. Returns library card, gym membership,
    utility bill, work badge, and a few receipts.
    """
    rng = random.Random(seed)
    wallet: List[Dict] = [
        make_library_card(identity, rng, today),
        make_gym_membership(identity, rng, today),
        make_utility_bill(identity, rng, today),
        make_work_badge(identity, rng, today),
    ]
    wallet.extend(make_receipts(identity, rng, count=3, today=today))
    return wallet


def render_text(document: Dict) -> str:
    """Render one document as a plain-text prop."""
    lines = [f"=== {document['kind'].upper().replace('_', ' ')} ==="]
    for key, value in document.items():
        if key == "kind":
            continue
        lines.append(f"  {key.replace('_', ' ')}: {value}")
    return "\n".join(lines)


def wallet_report(wallet: List[Dict]) -> Dict:
    """Summarize a wallet: counts by kind and the date range covered."""
    counts: Dict[str, int] = {}
    dates: List[str] = []
    for doc in wallet:
        counts[doc["kind"]] = counts.get(doc["kind"], 0) + 1
        for key in ("issued", "date", "period"):
            if key in doc:
                dates.append(str(doc[key]))
    return {
        "total": len(wallet),
        "by_kind": counts,
        "earliest": min(dates) if dates else None,
        "latest": max(dates) if dates else None,
    }
