"""Command-line interface for the Cover Identity Generator."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from . import export_json, export_markdown, generate, quiz
from . import aliases as aliases_mod
from . import burn as burn_mod
from . import checklists as checklists_mod
from . import comms as comms_mod
from . import consistency as cons_mod
from . import debrief as debrief_mod
from . import digital_footprint as fp_mod
from . import documents as docs_mod
from . import dossier as dossier_mod
from . import drill as drill_mod
from . import emergency as emergency_mod
from . import exporter as exporter_mod
from . import handler as handler_mod
from . import interrogation as iq_mod
from . import metrics as metrics_mod
from . import network as net_mod
from . import personas as personas_mod
from . import readiness as readiness_mod
from . import risk as risk_mod
from . import scenarios as scenarios_mod
from . import timeline as timeline_mod
from . import tradecraft as tc_mod
from . import vault as vault_mod


def _parse_today(raw: str | None) -> dt.date | None:
    if not raw:
        return None
    return dt.date.fromisoformat(raw)


# ---------------------------------------------------------------------------
# identity commands
# ---------------------------------------------------------------------------

def cmd_new(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed)
    if args.format == "json":
        text = export_json(ident)
    elif args.format == "markdown":
        text = export_markdown(ident)
    else:
        text = (
            f"{ident['name']} · {ident['age']} · {ident['date_of_birth']}\n"
            f"{ident['address']}\n"
            f"{ident['phone']} · {ident['email']}\n"
            f"{ident['occupation']} at {ident['employer']}\n"
        )
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"[+] Legend written to {args.out}")
    else:
        print(text)
    return 0


def cmd_memorize(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed)
    questions = quiz(ident)
    print("[*] Cover drill — answer from memory. Fail one, and you're burned.")
    for i, item in enumerate(questions, 1):
        ans = input(f"  {i}. {item['q']}: ").strip().lower()
        good = item["a"].lower()
        if ans == good:
            print("     ✓")
        else:
            print(f"     ✗  ({item['a']})")
    print("[*] Drill complete. Stay in character.")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed,
                     today=_parse_today(args.today))
    findings = cons_mod.audit(ident, today=_parse_today(args.today))
    if not findings:
        print("[+] Identity is internally consistent.")
        return 0
    for finding in findings:
        print(finding)
    worst = cons_mod.worst_severity(findings)
    print(f"[*] {len(findings)} finding(s); worst severity: {worst}")
    return 1 if worst == cons_mod.Severity.ERROR else 0


def cmd_timeline(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed,
                     today=_parse_today(args.today))
    print(timeline_mod.timeline_to_text(ident.get("timeline", [])))
    gaps = timeline_mod.gap_report(ident.get("timeline", []))
    if gaps:
        print()
        print("[!] Unexplained gaps:")
        for gap in gaps:
            print(f"    {gap['from_year']}–{gap['to_year']} ({gap['years']} years)")
    return 0


def cmd_persona(args: argparse.Namespace) -> int:
    if args.list:
        for name in personas_mod.list_personas():
            persona = personas_mod.get_persona(name)
            print(f"{name:<14} {persona['description']}")
        return 0
    if not args.name:
        print("error: give a persona name or --list", file=sys.stderr)
        return 2
    ident = generate(locale=args.locale, seed=args.seed)
    try:
        result = personas_mod.apply_persona(ident, args.name, seed=args.seed)
    except personas_mod.PersonaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"[+] Persona '{args.name}' applied to {result['name']}")
    print(f"    occupation: {result['occupation']}")
    print(f"    hobbies:    {', '.join(result['hobbies'])}")
    return 0


# ---------------------------------------------------------------------------
# dossier commands
# ---------------------------------------------------------------------------

def cmd_dossier(args: argparse.Namespace) -> int:
    today = _parse_today(args.today)
    dossier = dossier_mod.assemble(seed=args.seed, locale=args.locale,
                                   persona=args.persona, today=today)
    if args.format == "briefing":
        text = dossier_mod.render_briefing(dossier)
    else:
        text = exporter_mod.export(dossier, args.format)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"[+] Dossier written to {args.out}")
    else:
        print(text)
    return 0


def cmd_risk(args: argparse.Namespace) -> int:
    today = _parse_today(args.today)
    dossier = dossier_mod.assemble(seed=args.seed, locale=args.locale, today=today)
    report = dossier["risk"]
    print(f"Overall: {report['band']} (score {report['total']})")
    print(f"Fix first: {report['worst_factor']}")
    for factor, score in report["factors"].items():
        print(f"  {factor:<14} {score:.2f}")
    return 0


def cmd_drill(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed,
                     today=_parse_today(args.today))
    items = drill_mod.build_drill(ident)
    if args.study:
        for item in items:
            print(f"[{item.category}] {item.prompt}: {item.answer}")
        return 0
    # quiz mode: read answers from stdin, one per line
    answers = [line.strip() for line in sys.stdin]

    def answer_fn(prompt: str) -> str:
        for item in items:
            if item.prompt == prompt:
                idx = items.index(item)
                return answers[idx] if idx < len(answers) else ""
        return ""

    result = drill_mod.run_drill(ident, answer_fn)
    for item in result.items:
        mark = {"exact": "✓", "fuzzy": "~", "wrong": "✗"}[item["grade"]]
        print(f"  {mark} {item['prompt']}")
    print(f"[*] Burn meter: {result.meter}/100 — "
          f"{'PASS' if result.passed else 'FAIL'}")
    return 0 if result.passed else 1


def cmd_interrogate(args: argparse.Namespace) -> int:
    today = _parse_today(args.today)
    dossier = dossier_mod.assemble(seed=args.seed, locale=args.locale, today=today)
    probes = iq_mod.build_probes(dossier["identity"], dossier["network"],
                                 dossier["wallet"], seed=args.seed,
                                 max_probes=args.max_probes)
    print(f"[*] {len(probes)} probe(s), easiest first:")
    for i, probe in enumerate(probes, 1):
        print(f"  {i}. [{probe.facet}, difficulty {probe.difficulty}] "
              f"{probe.question}")
        print(f"     tell: {probe.tell}")
    return 0


# ---------------------------------------------------------------------------
# supporting material commands
# ---------------------------------------------------------------------------

def cmd_wallet(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed,
                     today=_parse_today(args.today))
    wallet = docs_mod.build_wallet(ident, seed=args.seed,
                                   today=_parse_today(args.today))
    for doc in wallet:
        print(docs_mod.render_text(doc))
        print()
    report = docs_mod.wallet_report(wallet)
    print(f"[*] {report['total']} documents; span "
          f"{report['earliest']} .. {report['latest']}")
    return 0


def cmd_network(args: argparse.Namespace) -> int:
    network = net_mod.build_network(seed=args.seed, size=args.size)
    print(net_mod.network_to_text(network))
    vouch = net_mod.vouch_list(network)
    print(f"\n[*] {len(vouch)} contact(s) close enough to vouch.")
    return 0


def cmd_footprint(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed,
                     today=_parse_today(args.today))
    footprint = fp_mod.build_footprint(ident, seed=args.seed,
                                       today=_parse_today(args.today))
    print("PROFILES:")
    for profile in footprint["profiles"]:
        print(f"  - {profile['platform']}: @{profile['handle']} "
              f"(since {profile['created']}, {profile['followers']} followers)")
    print("POSTS:")
    for post in footprint["posts"]:
        print(f"  - [{post['date']}] {post['text']}")
    report = fp_mod.footprint_report(footprint)
    print(f"\n[*] {report['platforms']} platform(s), "
          f"{report['total_followers']} followers total.")
    return 0


def cmd_tradecraft(args: argparse.Namespace) -> int:
    plan = tc_mod.operations_plan(seed=args.seed, today=_parse_today(args.today))
    drop = plan["dead_drop"]
    print(f"DEAD DROP '{drop.site_id}' at grid {drop.grid}: "
          f"{drop.container}, window {drop.loading_window}")
    print(f"  signal: {drop.signal}")
    print(f"  contingency: {drop.contingency}")
    bp = plan["brush_pass"]
    print(f"BRUSH PASS at {bp.location}, {bp.time}; cue: {bp.exchange_cue}")
    print("SDR:")
    for leg in plan["sdr"].legs:
        print(f"  - {leg.waypoint} ({leg.dwell_minutes} min): {leg.purpose}")
    problems = tc_mod.validate_sdr(plan["sdr"])
    if problems:
        print("[!] SDR problems:", "; ".join(problems))
    return 0


def cmd_burn(args: argparse.Namespace) -> int:
    plan = burn_mod.default_plan()
    if args.escalate:
        plan.escalate(steps=args.escalate)
    level = plan.current
    print(f"LEVEL: {level.name}")
    print(f"  trigger: {level.trigger}")
    print("  actions:")
    for action in level.actions:
        print(f"    - {action}")
    destroy = plan.cumulative_destroy()
    if destroy:
        print("  destroy:")
        for item in destroy:
            print(f"    - {item}")
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    import random
    schedule = comms_mod.build_schedule(random.Random(args.seed),
                                        per_week=args.per_week)
    print("CHECK-IN SCHEDULE:")
    for check in schedule:
        print(f"  - {check.day} {check.time} via {check.channel} "
              f"(backup: {check.backup_channel})")
    print("\nESCALATION LADDER:")
    for rung in comms_mod.ESCALATION_LADDER:
        print(f"  {rung['missed']} missed -> {rung['level']}: {rung['action']}")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    today = _parse_today(args.today) or dt.date.today()
    dash = handler_mod.HandlerDashboard()
    for i, seed in enumerate(args.seeds):
        name = args.names[i] if i < len(args.names) else f"legend-{seed}"
        dash.add_legend(name, dossier_mod.assemble(seed=seed, locale=args.locale,
                                                   today=today))
    if args.activate:
        try:
            dash.activate(args.activate, today)
        except handler_mod.HandlerError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    print(handler_mod.dashboard_to_text(dash, today))
    return 0


def cmd_checklist(args: argparse.Namespace) -> int:
    if args.list:
        for name in sorted(checklists_mod.CHECKLISTS):
            spec = checklists_mod.CHECKLISTS[name]
            print(f"{name:<14} {spec['purpose']}")
        return 0
    try:
        checklist = checklists_mod.get_checklist(args.name)
    except checklists_mod.ChecklistError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(checklist.to_text())
    print("\n[*] Walk it before you move. Required items block readiness.")
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    report = metrics_mod.quality_report(count=args.count, locale=args.locale,
                                        today=_parse_today(args.today))
    print(f"Sample size:        {report['sample_size']}")
    print(f"Consistency rate:   {report['consistency_rate']}")
    print("Risk distribution:")
    for band, count in sorted(report["risk_distribution"].items()):
        print(f"  {band:<12} {count}")
    div = report["diversity"]
    print("Diversity:")
    print(f"  names:       {div['name_diversity']}")
    print(f"  occupations: {div['occupation_diversity']}")
    print(f"  employers:   {div['employer_diversity']}")
    return 0


def cmd_debrief(args: argparse.Namespace) -> int:
    # Read debrief moments from stdin: "question | field | outcome" per line.
    debrief = debrief_mod.Debrief(args.legend)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            print(f"error: bad line {line!r}; expected 'question | field | outcome'",
                  file=sys.stderr)
            return 2
        try:
            debrief.add(parts[0], parts[1], parts[2])
        except debrief_mod.DebriefError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    report = debrief_mod.lessons_report(debrief)
    print(f"Legend: {report['legend']} — {report['moments']} moment(s)")
    for outcome, count in report["counts"].items():
        print(f"  {outcome:<10} {count}")
    if report["trouble_fields"]:
        print("Fields to fix:")
        for field in report["trouble_fields"]:
            print(f"  - {field}")
    print(f"\n[*] Recommendation: {report['recommendation']}")
    return 0


def cmd_readiness(args: argparse.Namespace) -> int:
    today = _parse_today(args.today)
    dossier = dossier_mod.assemble(seed=args.seed, locale=args.locale, today=today)
    report = readiness_mod.readiness_report(dossier, drill_meter=args.drill_meter)
    for gate in report["gates"]:
        mark = "✓" if gate["passed"] else "✗"
        print(f"  {mark} {gate['name']:<14} {gate['reason']}")
    print(f"\n[*] Verdict: {report['verdict'].upper()} "
          f"({report['failed_count']} gate(s) failed)")
    return 0 if report["verdict"] == "go" else 1


def cmd_scenarios(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed)
    scenarios = scenarios_mod.build_scenarios(ident, seed=args.seed,
                                              count=args.count)
    for scenario in scenarios:
        print(scenarios_mod.scenario_to_text(scenario))
        print()
    return 0


# ---------------------------------------------------------------------------
# vault commands
# ---------------------------------------------------------------------------

def cmd_vault_save(args: argparse.Namespace) -> int:
    ident = generate(locale=args.locale, seed=args.seed)
    vault = vault_mod.Vault()
    vault.unlock(args.passphrase, iterations=args.iterations)
    vault.put(args.name, ident)
    Path(args.out).write_bytes(vault.save())
    print(f"[+] Legend '{args.name}' saved to {args.out} (encrypted).")
    return 0


def cmd_vault_show(args: argparse.Namespace) -> int:
    data = Path(args.file).read_bytes()
    vault = vault_mod.Vault.load(data)
    try:
        vault.unlock(args.passphrase, iterations=args.iterations)
    except vault_mod.VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for name in vault.names():
        ident = vault.get(name)
        print(f"--- {name} ---")
        print(f"{ident['name']} · {ident['age']} · {ident['occupation']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="coverid",
        description="Generate fictional, internally consistent cover identities.",
        epilog="Example: coverid new --locale es_ES --seed 7 --format markdown --out legend.md",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="generate an identity")
    p_new.add_argument("--locale", default="en_US", help="Faker locale")
    p_new.add_argument("--seed", type=int, default=None, help="deterministic identity")
    p_new.add_argument("--format", default="plain", choices=["plain", "json", "markdown"])
    p_new.add_argument("--out", default=None, help="write to file")
    p_new.set_defaults(fn=cmd_new)

    p_mem = sub.add_parser("memorize", help="drill yourself on an identity")
    p_mem.add_argument("--locale", default="en_US")
    p_mem.add_argument("--seed", type=int, default=None)
    p_mem.set_defaults(fn=cmd_memorize)

    p_audit = sub.add_parser("audit", help="check an identity for contradictions")
    p_audit.add_argument("--locale", default="en_US")
    p_audit.add_argument("--seed", type=int, default=None)
    p_audit.add_argument("--today", default=None, help="reference date YYYY-MM-DD")
    p_audit.set_defaults(fn=cmd_audit)

    p_tl = sub.add_parser("timeline", help="show the dated life history")
    p_tl.add_argument("--locale", default="en_US")
    p_tl.add_argument("--seed", type=int, default=None)
    p_tl.add_argument("--today", default=None)
    p_tl.set_defaults(fn=cmd_timeline)

    p_persona = sub.add_parser("persona", help="list or apply archetypes")
    p_persona.add_argument("name", nargs="?", default=None)
    p_persona.add_argument("--list", action="store_true")
    p_persona.add_argument("--locale", default="en_US")
    p_persona.add_argument("--seed", type=int, default=None)
    p_persona.set_defaults(fn=cmd_persona)

    p_dossier = sub.add_parser("dossier", help="assemble the complete dossier")
    p_dossier.add_argument("--locale", default="en_US")
    p_dossier.add_argument("--seed", type=int, default=None)
    p_dossier.add_argument("--persona", default=None)
    p_dossier.add_argument("--today", default=None)
    p_dossier.add_argument("--format", default="briefing",
                           choices=["briefing", "json", "markdown",
                                    "cheat-sheet", "redacted"])
    p_dossier.add_argument("--out", default=None)
    p_dossier.set_defaults(fn=cmd_dossier)

    p_risk = sub.add_parser("risk", help="exposure-risk assessment")
    p_risk.add_argument("--locale", default="en_US")
    p_risk.add_argument("--seed", type=int, default=None)
    p_risk.add_argument("--today", default=None)
    p_risk.set_defaults(fn=cmd_risk)

    p_drill = sub.add_parser("drill", help="scored memorization drill")
    p_drill.add_argument("--locale", default="en_US")
    p_drill.add_argument("--seed", type=int, default=None)
    p_drill.add_argument("--today", default=None)
    p_drill.add_argument("--study", action="store_true",
                         help="print questions and answers instead of quizzing")
    p_drill.set_defaults(fn=cmd_drill)

    p_iq = sub.add_parser("interrogate", help="adversarial probe list")
    p_iq.add_argument("--locale", default="en_US")
    p_iq.add_argument("--seed", type=int, default=None)
    p_iq.add_argument("--today", default=None)
    p_iq.add_argument("--max-probes", type=int, default=8)
    p_iq.set_defaults(fn=cmd_interrogate)

    p_wallet = sub.add_parser("wallet", help="fabricate the paper trail")
    p_wallet.add_argument("--locale", default="en_US")
    p_wallet.add_argument("--seed", type=int, default=None)
    p_wallet.add_argument("--today", default=None)
    p_wallet.set_defaults(fn=cmd_wallet)

    p_net = sub.add_parser("network", help="build the social web")
    p_net.add_argument("--seed", type=int, default=None)
    p_net.add_argument("--size", type=int, default=5)
    p_net.set_defaults(fn=cmd_network)

    p_fp = sub.add_parser("footprint", help="build the digital footprint")
    p_fp.add_argument("--locale", default="en_US")
    p_fp.add_argument("--seed", type=int, default=None)
    p_fp.add_argument("--today", default=None)
    p_fp.set_defaults(fn=cmd_footprint)

    p_tc = sub.add_parser("tradecraft", help="fictional operations plan")
    p_tc.add_argument("--seed", type=int, default=None)
    p_tc.add_argument("--today", default=None)
    p_tc.set_defaults(fn=cmd_tradecraft)

    p_burn = sub.add_parser("burn", help="compromise response plan")
    p_burn.add_argument("--escalate", type=int, default=0,
                        help="show the plan N levels up")
    p_burn.set_defaults(fn=cmd_burn)

    p_sched = sub.add_parser("schedule", help="check-in schedule and ladder")
    p_sched.add_argument("--seed", type=int, default=None)
    p_sched.add_argument("--per-week", type=int, default=2)
    p_sched.set_defaults(fn=cmd_schedule)

    p_dash = sub.add_parser("dashboard", help="multi-legend status board")
    p_dash.add_argument("--seeds", type=int, nargs="+", required=True,
                        help="one seed per legend")
    p_dash.add_argument("--names", nargs="*", default=[],
                        help="optional names matching the seeds")
    p_dash.add_argument("--activate", default=None,
                        help="legend name to put into rotation")
    p_dash.add_argument("--locale", default="en_US")
    p_dash.add_argument("--today", default=None)
    p_dash.set_defaults(fn=cmd_dashboard)

    p_cl = sub.add_parser("checklist", help="show a pre-action checklist")
    p_cl.add_argument("name", nargs="?", default="pre-meeting")
    p_cl.add_argument("--list", action="store_true")
    p_cl.set_defaults(fn=cmd_checklist)

    p_met = sub.add_parser("metrics", help="generator quality metrics")
    p_met.add_argument("--count", type=int, default=20)
    p_met.add_argument("--locale", default="en_US")
    p_met.add_argument("--today", default=None)
    p_met.set_defaults(fn=cmd_metrics)

    p_db = sub.add_parser("debrief", help="post-operation review (stdin)")
    p_db.add_argument("legend", help="legend name being debriefed")
    p_db.set_defaults(fn=cmd_debrief)

    p_ready = sub.add_parser("readiness", help="pre-deployment go/no-go gates")
    p_ready.add_argument("--locale", default="en_US")
    p_ready.add_argument("--seed", type=int, default=None)
    p_ready.add_argument("--today", default=None)
    p_ready.add_argument("--drill-meter", type=int, default=100,
                         help="the operator's current drill score (0-100)")
    p_ready.set_defaults(fn=cmd_readiness)

    p_scen = sub.add_parser("scenarios", help="rehearsal scenario cards")
    p_scen.add_argument("--locale", default="en_US")
    p_scen.add_argument("--seed", type=int, default=None)
    p_scen.add_argument("--count", type=int, default=3)
    p_scen.set_defaults(fn=cmd_scenarios)

    p_vs = sub.add_parser("vault-save", help="encrypt a legend into a vault file")
    p_vs.add_argument("name", help="legend name inside the vault")
    p_vs.add_argument("--passphrase", required=True)
    p_vs.add_argument("--iterations", type=int, default=vault_mod.KDF_ITERATIONS)
    p_vs.add_argument("--locale", default="en_US")
    p_vs.add_argument("--seed", type=int, default=None)
    p_vs.add_argument("--out", required=True)
    p_vs.set_defaults(fn=cmd_vault_save)

    p_vsh = sub.add_parser("vault-show", help="decrypt and list a vault file")
    p_vsh.add_argument("file")
    p_vsh.add_argument("--passphrase", required=True)
    p_vsh.add_argument("--iterations", type=int, default=vault_mod.KDF_ITERATIONS)
    p_vsh.set_defaults(fn=cmd_vault_show)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
