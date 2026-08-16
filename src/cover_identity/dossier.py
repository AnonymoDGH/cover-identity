"""Complete dossier assembly for a cover identity.

The individual modules each build one facet of a legend -- the identity,
the paper trail, the social web, the digital footprint, the timeline.
This module pulls them all together into a single dossier dict and renders
it as a readable briefing document, so a handler gets one artifact instead
of ten.

assemble() is deterministic under a seed: the same seed and persona always
produce the same dossier, which makes the package testable and lets two
handlers rebuild an identical legend from a shared seed.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Dict, Optional

from . import appearance
from . import consistency as cons
from . import corpus
from . import digital_footprint as fp
from . import documents as docs
from . import drill
from . import emergency
from . import comms
from . import finance
from . import habits
from . import languages
from . import medical
from . import network as net
from . import personas
from . import residence
from . import risk
from . import speech
from . import timeline as tl
from . import tradecraft
from . import travel
from . import vehicles
from . import generate

__all__ = [
    "assemble",
    "render_briefing",
    "dossier_summary",
]


def assemble(seed: Optional[int] = None, locale: str = "en_US",
             persona: Optional[str] = None,
             today: Optional[dt.date] = None) -> Dict:
    """Build a complete, internally consistent dossier.

    Args:
        seed: Deterministic seed shared by every sub-generator.
        locale: Faker locale for the base identity.
        persona: Optional archetype name to bias the legend.
        today: Reference date; defaults to the real today.

    Returns:
        A dict with the identity plus wallet, network, footprint,
        timeline, drill, consistency findings, and a risk report.
    """
    identity = generate(locale=locale, seed=seed, today=today)
    if persona is not None:
        identity = personas.apply_persona(identity, persona, seed=seed)

    wallet = docs.build_wallet(identity, seed=seed, today=today)
    network_shape = identity.get("persona", {}).get("network_shape", "medium")
    network = net.build_network(seed=seed,
                                size=personas.network_size_for(network_shape))
    footprint = fp.build_footprint(identity, seed=seed, today=today)
    financial = finance.build_financial_history(identity, seed=seed, today=today)
    trips = travel.build_travel_history(identity, seed=seed, today=today)

    sub_rng = random.Random(seed)
    med_profile = medical.build_medical_profile(
        sub_rng, identity["age"], today_year=(today or dt.date.today()).year)
    home = residence.build_residence(sub_rng, identity["address"])
    safe_houses = residence.build_safe_houses(sub_rng, count=2)
    hood = residence.build_neighborhood(sub_rng)
    desc = appearance.build_description(sub_rng, identity["age"])
    speech_kit = speech.build_speech_kit(sub_rng, identity)
    duress = emergency.build_duress_codes(sub_rng, count=3)
    ops = tradecraft.operations_plan(seed=seed, today=today)
    routine = habits.build_routine(sub_rng, identity["occupation"])
    habit_set = habits.build_habits(sub_rng)
    lang_profile = languages.build_language_profile(sub_rng, extra_languages=1)
    phrases = languages.local_phrases(sub_rng, count=3)
    vehicle = vehicles.build_vehicle(sub_rng)
    routes = vehicles.build_routes(sub_rng, count=3)
    schedule = comms.build_schedule(sub_rng, per_week=2)

    findings = cons.audit(identity, today=today)
    report = risk.assess(identity, footprint, network, wallet, today=today)
    drill_items = drill.build_drill(identity)

    return {
        "identity": identity,
        "persona": persona,
        "wallet": wallet,
        "network": network,
        "footprint": footprint,
        "finance": financial,
        "travel": trips,
        "medical": med_profile,
        "residence": home,
        "safe_houses": safe_houses,
        "neighborhood": hood,
        "appearance": desc,
        "speech_kit": speech_kit,
        "duress_codes": duress,
        "operations": ops,
        "routine": routine,
        "habits": habit_set,
        "languages": lang_profile,
        "local_phrases": phrases,
        "vehicle": vehicle,
        "routes": routes,
        "comms_schedule": schedule,
        "drill": [
            {"prompt": i.prompt, "answer": i.answer, "category": i.category}
            for i in drill_items
        ],
        "consistency": [str(f) for f in findings],
        "risk": report,
    }


def render_briefing(dossier: Dict) -> str:
    """Render a dossier as a human-readable briefing document."""
    ident = dossier["identity"]
    lines = [
        "=" * 60,
        "COVER DOSSIER",
        "=" * 60,
        "",
        f"NAME:       {ident['name']}",
        f"AGE:        {ident['age']} (born {ident['date_of_birth']})",
        f"ADDRESS:    {ident['address']}",
        f"PHONE:      {ident['phone']}",
        f"EMAIL:      {ident['email']}",
        f"OCCUPATION: {ident['occupation']} at {ident['employer']}",
    ]
    if dossier.get("persona"):
        lines.append(f"PERSONA:    {dossier['persona']}")
    lines += ["", "--- BACKSTORY ---", "", ident["backstory"], ""]

    lines += ["--- TIMELINE ---", ""]
    lines.append(tl.timeline_to_text(ident.get("timeline", [])))
    lines.append("")

    lines += ["--- PAPER TRAIL ---", ""]
    for doc in dossier["wallet"]:
        lines.append(docs.render_text(doc))
        lines.append("")

    lines += ["--- NETWORK ---", ""]
    lines.append(net.network_to_text(dossier["network"]))
    lines.append("")

    fin = dossier["finance"]
    lines += [
        "--- FINANCES ---",
        "",
        f"Income: {fin['monthly_income']}/month from {fin['income_source']}",
        f"Credit: {fin['credit']['score']} ({fin['credit']['rating']})",
    ]
    lines.append("")

    lines += ["--- TRAVEL ---", ""]
    for trip in dossier["travel"]:
        lines.append(f"- {trip['start']}: {trip['destination']} "
                     f"({trip['purpose']}, {trip['days']} days)")
    lines.append("")

    lines += ["--- MEDICAL ---", "", dossier["medical"].summary(), ""]

    lines += [
        "--- RESIDENCE ---",
        "",
        residence.residence_brief(dossier["residence"],
                                  dossier["safe_houses"],
                                  dossier["neighborhood"]),
        "",
    ]

    lines += [
        "--- APPEARANCE ---",
        "",
        dossier["appearance"].to_text(),
        "",
    ]

    lines += ["--- DURESS CODES ---", ""]
    for code in dossier["duress_codes"]:
        lines.append(f"- say '{code.phrase}' ({code.channel}) -> {code.meaning}")
    lines.append("")

    lines += [emergency.protocol_to_text(emergency.build_emergency_protocol()), ""]

    lines += [habits.routine_to_text(dossier["routine"]), ""]
    lines += ["HABITS:"]
    lines += [f"  - {fact}" for fact in dossier["habits"].to_list()]
    lines.append("")

    lines += [languages.profile_to_text(dossier["languages"],
                                        dossier["local_phrases"]), ""]

    lines += [vehicles.vehicle_card(dossier["vehicle"], ident["name"]), ""]
    lines += ["ROUTES TO KNOW COLD:"]
    lines += [f"  - {route.describe()}" for route in dossier["routes"]]
    lines.append("")

    lines += ["CHECK-IN SCHEDULE:"]
    for check in dossier["comms_schedule"]:
        lines.append(f"  - {check.day} {check.time} via {check.channel} "
                     f"(backup: {check.backup_channel})")
    lines.append("")

    lines += ["--- MEMORY ANCHORS ---", ""]
    for item in dossier["drill"]:
        if item["category"] == "anchor":
            lines.append(f"- {item['prompt']}: {item['answer']}")
    lines.append("")

    report = dossier["risk"]
    lines += [
        "--- RISK ASSESSMENT ---",
        "",
        f"Overall: {report['band']} (score {report['total']})",
        f"Fix first: {report['worst_factor']}",
    ]
    for factor, score in report["factors"].items():
        lines.append(f"  {factor:<14} {score:.2f}")
    if dossier["consistency"]:
        lines.append("")
        lines.append("Consistency findings:")
        lines.extend(f"  {f}" for f in dossier["consistency"])
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def dossier_summary(dossier: Dict) -> Dict:
    """A compact machine-readable summary of a dossier."""
    ident = dossier["identity"]
    return {
        "name": ident["name"],
        "persona": dossier.get("persona"),
        "documents": len(dossier["wallet"]),
        "contacts": len(dossier["network"]),
        "platforms": len(dossier["footprint"]["profiles"]),
        "trips": len(dossier["travel"]),
        "monthly_income": dossier["finance"]["monthly_income"],
        "safe_houses": len(dossier["safe_houses"]),
        "duress_codes": len(dossier["duress_codes"]),
        "drill_questions": len(dossier["drill"]),
        "risk_band": dossier["risk"]["band"],
        "risk_total": dossier["risk"]["total"],
        "consistency_issues": len(dossier["consistency"]),
    }
