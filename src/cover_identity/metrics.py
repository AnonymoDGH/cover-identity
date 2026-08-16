"""Legend quality metrics across many generated identities.

A single legend can be judged by the risk module; a *generator* is judged
by the population it produces. This module samples many identities under
different seeds and reports aggregate quality: how often they are
internally consistent, how the risk scores distribute, and how diverse
the names and occupations are.

Low diversity is itself a red flag: if every seeded legend comes out a
locksmith named Mara, the generator is leaking structure. This module
measures that with simple entropy-style counts.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from . import consistency as cons_mod
from . import dossier as dossier_mod
from . import risk as risk_mod

__all__ = [
    "sample_legends",
    "consistency_rate",
    "risk_distribution",
    "diversity_report",
    "quality_report",
]


def sample_legends(count: int = 20, locale: str = "en_US",
                   today: Optional[dt.date] = None) -> List[Dict]:
    """Generate a batch of identities, one per seed 0..count-1."""
    if count < 1:
        raise ValueError("count must be >= 1")
    return [dossier_mod.assemble(seed=i, locale=locale, today=today)
            for i in range(count)]


def consistency_rate(legends: List[Dict]) -> float:
    """Fraction of legends with zero consistency errors."""
    if not legends:
        return 0.0
    clean = 0
    for legend in legends:
        errors = [f for f in legend.get("consistency", [])
                  if str(f).startswith("[ERROR]")]
        if not errors:
            clean += 1
    return round(clean / len(legends), 3)


def risk_distribution(legends: List[Dict]) -> Dict[str, int]:
    """Count legends per risk band."""
    bands: Dict[str, int] = {}
    for legend in legends:
        band = legend.get("risk", {}).get("band", "unknown")
        bands[band] = bands.get(band, 0) + 1
    return bands


def _distinct_ratio(values: List[str]) -> float:
    if not values:
        return 0.0
    return round(len(set(values)) / len(values), 3)


def diversity_report(legends: List[Dict]) -> Dict:
    """How varied the population is across names, jobs, and employers.

    A ratio near 1.0 means high diversity; near 0 means the generator is
    stuck in a rut.
    """
    names = [l["identity"]["name"] for l in legends]
    occupations = [l["identity"]["occupation"] for l in legends]
    employers = [l["identity"]["employer"] for l in legends]
    return {
        "name_diversity": _distinct_ratio(names),
        "occupation_diversity": _distinct_ratio(occupations),
        "employer_diversity": _distinct_ratio(employers),
    }


def quality_report(count: int = 20, locale: str = "en_US",
                   today: Optional[dt.date] = None) -> Dict:
    """A full generator-quality report over a seeded sample."""
    legends = sample_legends(count, locale, today)
    return {
        "sample_size": len(legends),
        "consistency_rate": consistency_rate(legends),
        "risk_distribution": risk_distribution(legends),
        "diversity": diversity_report(legends),
    }
