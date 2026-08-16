"""Financial history for a cover identity.

Money leaves the deepest trail. A legend needs a plausible income story,
a bank that would answer a callback, and spending habits that match the
occupation. This module fabricates that financial texture: an income
source consistent with the job, a monthly budget broken into boring
categories, a handful of recurring transactions, and a credit profile that
is deliberately average.

An average credit profile is the goal. Excellent credit invites attention;
no credit at all invites more. A middling score with a long, dull history
is the camouflage.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Dict, List, Optional

from . import corpus

__all__ = [
    "BUDGET_CATEGORIES",
    "income_for_occupation",
    "build_budget",
    "build_transactions",
    "credit_profile",
    "build_financial_history",
    "finance_report",
]

#: Monthly budget categories, in rough order of size.
BUDGET_CATEGORIES: List[str] = [
    "rent", "groceries", "utilities", "transport", "phone",
    "insurance", "savings", "misc",
]

#: Occupation sector -> plausible monthly income range.
_INCOME_RANGES: Dict[str, tuple] = {
    "trades": (2600, 4200),
    "logistics": (2400, 3800),
    "knowledge": (2800, 4600),
    "hospitality": (2000, 3200),
    "creative": (1800, 3600),
}


def _sector_for_occupation(occupation: str) -> str:
    """Find which sector an occupation belongs to."""
    for sector, jobs in corpus.OCCUPATIONS.items():
        if occupation in jobs:
            return sector
    return "logistics"  # safe default


def income_for_occupation(occupation: str, rng: random.Random) -> int:
    """A plausible monthly income for the given occupation."""
    sector = _sector_for_occupation(occupation)
    lo, hi = _INCOME_RANGES[sector]
    return rng.randrange(lo, hi + 1)


def build_budget(income: int, rng: random.Random) -> Dict[str, int]:
    """Break an income into a boring monthly budget that sums below income.

    Rent takes the largest share; savings is always present (a cover with
    no savings looks desperate). The remainder lands in misc.
    """
    if income <= 0:
        raise ValueError("income must be positive")
    budget: Dict[str, int] = {}
    budget["rent"] = int(income * rng.uniform(0.28, 0.36))
    budget["groceries"] = int(income * rng.uniform(0.12, 0.18))
    budget["utilities"] = int(income * rng.uniform(0.06, 0.10))
    budget["transport"] = int(income * rng.uniform(0.05, 0.09))
    budget["phone"] = rng.randrange(20, 60)
    budget["insurance"] = rng.randrange(60, 160)
    budget["savings"] = int(income * rng.uniform(0.08, 0.15))
    spent = sum(budget.values())
    budget["misc"] = max(50, income - spent - rng.randrange(50, 150))
    return budget


def build_transactions(rng: random.Random, count: int = 8,
                       today: Optional[dt.date] = None) -> List[Dict]:
    """A handful of recurring transactions consistent with the budget."""
    today = today or dt.date.today()
    transactions: List[Dict] = []
    vendors = {
        "groceries": ["the corner market", "the co-op", "the weekend stall"],
        "transport": ["the transit authority", "the fuel station", "the bike shop"],
        "utilities": ["City Water & Power", "Coastal Energy", "Metro Gas Co."],
        "misc": ["the hardware store", "the bookshop", "the cafe"],
    }
    for i in range(count):
        category = rng.choice(list(vendors))
        days_ago = rng.randrange(1, 30)
        transactions.append({
            "category": category,
            "vendor": rng.choice(vendors[category]),
            "amount": f"{rng.randrange(5, 120)}.{rng.randrange(0, 99):02d}",
            "date": (today - dt.timedelta(days=days_ago)).isoformat(),
            "recurring": rng.random() < 0.6,
        })
    transactions.sort(key=lambda t: t["date"])
    return transactions


def credit_profile(rng: random.Random, age: int) -> Dict:
    """A deliberately average credit profile scaled to the cover's age.

    The score sits in the middle band; history length grows with age so a
    young cover does not claim twenty years of credit.
    """
    history_years = max(1, min(age - 18, rng.randrange(3, 20)))
    score = rng.randrange(620, 740)  # solidly average
    return {
        "score": score,
        "history_years": history_years,
        "open_accounts": rng.randrange(2, 6),
        "missed_payments": rng.randrange(0, 2),
        "rating": "average",
    }


def build_financial_history(identity: Dict, seed: Optional[int] = None,
                            today: Optional[dt.date] = None) -> Dict:
    """Assemble a full, deterministic financial history for one identity."""
    rng = random.Random(seed)
    income = income_for_occupation(identity.get("occupation", ""), rng)
    return {
        "income_source": identity.get("employer", "an unnamed firm"),
        "monthly_income": income,
        "budget": build_budget(income, rng),
        "transactions": build_transactions(rng, count=8, today=today),
        "credit": credit_profile(rng, identity.get("age", 35)),
    }


def finance_report(history: Dict) -> Dict:
    """Summarize a financial history: does the budget balance?"""
    budget = history.get("budget", {})
    income = history.get("monthly_income", 0)
    total_spent = sum(budget.values())
    return {
        "monthly_income": income,
        "monthly_outgo": total_spent,
        "surplus": income - total_spent,
        "balanced": total_spent <= income,
        "credit_score": history.get("credit", {}).get("score"),
    }
