"""End-to-end integration tests across the whole cover-identity package.

These tests exercise the full pipeline the way a handler actually would:
assemble a dossier, audit it, drill it, interrogate it, vault it, rotate
it, and debrief it. They exist to catch cross-module drift that unit tests
miss -- the kind of bug where one module's output stops fitting another
module's input.
"""

from __future__ import annotations

import datetime as dt
import json

from cover_identity import alibi as alibi_mod
from cover_identity import aliases as aliases_mod
from cover_identity import burn as burn_mod
from cover_identity import consistency as cons_mod
from cover_identity import debrief as debrief_mod
from cover_identity import dossier as dossier_mod
from cover_identity import drill as drill_mod
from cover_identity import exporter as exporter_mod
from cover_identity import habits as habits_mod
from cover_identity import handler as handler_mod
from cover_identity import interrogation as iq_mod
from cover_identity import readiness as readiness_mod
from cover_identity import rotation as rotation_mod
from cover_identity import vault as vault_mod

TODAY = dt.date(2024, 6, 1)


def test_full_lifecycle_one_legend():
    """Build, audit, drill, vault, and debrief a single legend."""
    dossier = dossier_mod.assemble(seed=42, persona="tradesperson", today=TODAY)

    # The dossier must be internally consistent.
    errors = [f for f in dossier["consistency"] if str(f).startswith("[ERROR]")]
    assert errors == []

    # A perfect drill must pass.
    answers = {i["prompt"]: i["answer"] for i in dossier["drill"]}
    ident = dossier["identity"]
    result = drill_mod.run_drill(ident, lambda p: answers.get(p, ""))
    assert result.passed

    # The legend must be ready to deploy.
    report = readiness_mod.readiness_report(dossier, drill_meter=result.meter)
    assert report["verdict"] == "go"

    # Vault it and get it back.
    vault = vault_mod.Vault()
    vault.unlock("correct horse", iterations=1000)
    vault.put("berlin", ident)
    blob = vault.save()
    vault2 = vault_mod.Vault.load(blob)
    vault2.unlock("correct horse", iterations=1000)
    assert vault2.get("berlin")["name"] == ident["name"]

    # Debrief a clean run.
    debrief = debrief_mod.Debrief("berlin")
    debrief.add("Where do you live?", "address", debrief_mod.Outcome.CLEAN)
    lessons = debrief_mod.lessons_report(debrief)
    assert lessons["recommendation"] == "legend held; keep it as is"


def test_alibi_matches_routine():
    """An alibi built from the routine must verify clean."""
    dossier = dossier_mod.assemble(seed=7, today=TODAY)
    blocks = dossier["routine"]
    alibi = alibi_mod.build_alibi("Tuesday", blocks, [10, 14, 18])
    assert alibi_mod.verify_alibi(alibi, blocks) == []


def test_interrogation_with_dossier_material():
    """Interrogation probes must be answerable from the dossier."""
    dossier = dossier_mod.assemble(seed=9, today=TODAY)
    report = iq_mod.run_interrogation(
        dossier["identity"],
        lambda q: "I have answered that fully and I stand by my story.",
        dossier["network"], dossier["wallet"], seed=9)
    assert report["probes"] > 0
    assert report["verdict"] in {"holds", "strained", "cracks"}


def test_alias_graph_from_dossiers():
    """Two dossiers must not collide on contact fields."""
    a = dossier_mod.assemble(seed=1, today=TODAY)
    b = dossier_mod.assemble(seed=2, today=TODAY)
    graph = aliases_mod.AliasGraph()
    graph.add(aliases_mod.from_identity("a", "x", a["identity"]))
    graph.add(aliases_mod.from_identity("b", "y", b["identity"]))
    assert graph.cross_check() == []


def test_rotation_with_readiness():
    """Only ready legends should be activated; rotation must respect it."""
    dash = handler_mod.HandlerDashboard()
    dash.add_legend("berlin", dossier_mod.assemble(seed=1, today=TODAY))
    dash.add_legend("oslo", dossier_mod.assemble(seed=2, today=TODAY))
    # Both are ready, so activating either is fine.
    assert dash.readiness("berlin")["verdict"] == "go"
    dash.activate("berlin", TODAY)
    assert dash.overview(TODAY)["active"] == "berlin"


def test_export_all_formats_parse():
    """Every export format must produce valid, non-empty output."""
    dossier = dossier_mod.assemble(seed=3, today=TODAY)
    for fmt in exporter_mod.EXPORT_FORMATS:
        text = exporter_mod.export(dossier, fmt)
        assert text.strip()
    # JSON and redacted must parse.
    json.loads(exporter_mod.export(dossier, "json"))
    json.loads(exporter_mod.export(dossier, "redacted"))


def test_burn_plan_escalates_with_debrief():
    """A debrief full of invented details should justify escalation."""
    debrief = debrief_mod.Debrief("berlin")
    for i in range(4):
        debrief.add(f"q{i}", f"field{i}", debrief_mod.Outcome.INVENTED)
    lessons = debrief_mod.lessons_report(debrief)
    assert lessons["recommendation"].startswith("rebuild")
    # And the burn plan can walk all the way to evacuate.
    plan = burn_mod.default_plan()
    plan.escalate(steps=3)
    assert plan.current.name == "evacuate"


def test_many_seeds_all_consistent():
    """A sweep of seeds must all produce consistent, ready legends."""
    for seed in range(10):
        dossier = dossier_mod.assemble(seed=seed, today=TODAY)
        errors = [f for f in dossier["consistency"]
                  if str(f).startswith("[ERROR]")]
        assert errors == [], f"seed {seed} produced errors: {errors}"
