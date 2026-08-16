"""Tests for the expanded coverid CLI."""

from __future__ import annotations

import json

import pytest

from cover_identity.cli import main


def test_new_plain(capsys):
    assert main(["new", "--seed", "42"]) == 0
    out = capsys.readouterr().out
    assert "·" in out


def test_new_json(capsys):
    assert main(["new", "--seed", "42", "--format", "json"]) == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "name" in parsed


def test_new_to_file(tmp_path, capsys):
    out_file = tmp_path / "legend.md"
    assert main(["new", "--seed", "42", "--format", "markdown",
                 "--out", str(out_file)]) == 0
    assert out_file.exists()
    assert "[+] Legend written" in capsys.readouterr().out


def test_audit_clean(capsys):
    rc = main(["audit", "--seed", "42", "--today", "2024-06-01"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "consistent" in out


def test_timeline(capsys):
    assert main(["timeline", "--seed", "42", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "born" in out


def test_persona_list(capsys):
    assert main(["persona", "--list"]) == 0
    out = capsys.readouterr().out
    assert "tradesperson" in out


def test_persona_apply(capsys):
    assert main(["persona", "clerk", "--seed", "42"]) == 0
    out = capsys.readouterr().out
    assert "applied" in out


def test_persona_unknown(capsys):
    rc = main(["persona", "nonexistent", "--seed", "42"])
    assert rc == 2
    assert "error" in capsys.readouterr().err


def test_persona_no_args(capsys):
    rc = main(["persona"])
    assert rc == 2


def test_dossier_briefing(capsys):
    assert main(["dossier", "--seed", "42", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "COVER DOSSIER" in out


def test_dossier_json_to_file(tmp_path, capsys):
    out_file = tmp_path / "dossier.json"
    assert main(["dossier", "--seed", "42", "--today", "2024-06-01",
                 "--format", "json", "--out", str(out_file)]) == 0
    parsed = json.loads(out_file.read_text(encoding="utf-8"))
    assert "identity" in parsed


def test_dossier_cheat_sheet(capsys):
    assert main(["dossier", "--seed", "42", "--today", "2024-06-01",
                 "--format", "cheat-sheet"]) == 0
    out = capsys.readouterr().out
    assert "CHEAT SHEET" in out


def test_risk(capsys):
    assert main(["risk", "--seed", "42", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "Overall:" in out
    assert "Fix first:" in out


def test_drill_study(capsys):
    assert main(["drill", "--seed", "42", "--today", "2024-06-01",
                 "--study"]) == 0
    out = capsys.readouterr().out
    assert "Full name" in out


def test_drill_quiz_perfect(capsys, monkeypatch):
    # Feed perfect answers via stdin by pre-computing them.
    from cover_identity import drill as drill_mod, generate
    ident = generate(seed=42, today=__import__("datetime").date(2024, 6, 1))
    items = drill_mod.build_drill(ident)
    answers = "\n".join(i.answer for i in items)
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(answers))
    rc = main(["drill", "--seed", "42", "--today", "2024-06-01"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "PASS" in out


def test_interrogate(capsys):
    assert main(["interrogate", "--seed", "42", "--today", "2024-06-01",
                 "--max-probes", "4"]) == 0
    out = capsys.readouterr().out
    assert "probe(s)" in out


def test_wallet(capsys):
    assert main(["wallet", "--seed", "42", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "LIBRARY CARD" in out


def test_network(capsys):
    assert main(["network", "--seed", "42", "--size", "4"]) == 0
    out = capsys.readouterr().out
    assert "vouch" in out


def test_footprint(capsys):
    assert main(["footprint", "--seed", "42", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "PROFILES:" in out


def test_tradecraft(capsys):
    assert main(["tradecraft", "--seed", "42", "--today", "2024-06-01"]) == 0
    out = capsys.readouterr().out
    assert "DEAD DROP" in out
    assert "BRUSH PASS" in out


def test_burn_base(capsys):
    assert main(["burn"]) == 0
    out = capsys.readouterr().out
    assert "LEVEL: lay-low" in out


def test_burn_escalated(capsys):
    assert main(["burn", "--escalate", "3"]) == 0
    out = capsys.readouterr().out
    assert "LEVEL: evacuate" in out


def test_schedule(capsys):
    assert main(["schedule", "--seed", "42", "--per-week", "3"]) == 0
    out = capsys.readouterr().out
    assert "CHECK-IN SCHEDULE" in out
    assert "ESCALATION LADDER" in out


def test_vault_roundtrip(tmp_path, capsys):
    vault_file = tmp_path / "legends.vault"
    assert main(["vault-save", "berlin", "--passphrase", "hunter2",
                 "--iterations", "1000", "--seed", "42",
                 "--out", str(vault_file)]) == 0
    assert vault_file.exists()
    capsys.readouterr()
    assert main(["vault-show", str(vault_file), "--passphrase", "hunter2",
                 "--iterations", "1000"]) == 0
    out = capsys.readouterr().out
    assert "berlin" in out


def test_vault_wrong_passphrase(tmp_path, capsys):
    vault_file = tmp_path / "legends.vault"
    main(["vault-save", "berlin", "--passphrase", "hunter2",
          "--iterations", "1000", "--seed", "42", "--out", str(vault_file)])
    capsys.readouterr()
    rc = main(["vault-show", str(vault_file), "--passphrase", "wrong",
               "--iterations", "1000"])
    assert rc == 1
    assert "error" in capsys.readouterr().err
