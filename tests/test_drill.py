"""Tests for cover_identity.drill -- scored memorization drill."""

from __future__ import annotations

from cover_identity import drill
from cover_identity import generate


def _ident():
    return generate(seed=42)


def test_normalize_strips_punctuation():
    assert drill.normalize("  Hello, World! ") == "hello world"


def test_grade_exact():
    assert drill.grade_answer("Ada Lovelace", "ada lovelace") == drill.Grade.EXACT
    assert drill.grade_answer("1985-03-14", "1985-03-14") == drill.Grade.EXACT


def test_grade_fuzzy_on_key_token():
    assert drill.grade_answer("Ada Lovelace", "it's Lovelace") == drill.Grade.FUZZY


def test_grade_wrong():
    assert drill.grade_answer("Ada Lovelace", "no idea") == drill.Grade.WRONG
    assert drill.grade_answer("Ada Lovelace", "") == drill.Grade.WRONG


def test_build_drill_covers_basics_and_anchors():
    ident = _ident()
    items = drill.build_drill(ident)
    prompts = [i.prompt for i in items]
    assert "Full name" in prompts
    assert any("maiden" in p for p in prompts)
    categories = {i.category for i in items}
    assert "basics" in categories and "anchor" in categories


def test_build_drill_includes_timeline_when_present():
    ident = _ident()
    items = drill.build_drill(ident)
    assert any(i.category == "timeline" for i in items)


def test_run_drill_perfect_score():
    ident = _ident()
    answers = {i.prompt: i.answer for i in drill.build_drill(ident)}
    result = drill.run_drill(ident, lambda p: answers[p])
    assert result.meter == 100
    assert result.passed


def test_run_drill_all_wrong():
    ident = _ident()
    result = drill.run_drill(ident, lambda p: "totally wrong answer")
    assert result.meter == 0
    assert not result.passed


def test_burn_meter_weighting():
    # Anchor misses hurt more than basics misses.
    items = [
        {"grade": drill.Grade.WRONG, "category": "anchor"},
        {"grade": drill.Grade.EXACT, "category": "basics"},
    ]
    meter_anchor_miss = drill.burn_meter(items)
    items2 = [
        {"grade": drill.Grade.EXACT, "category": "anchor"},
        {"grade": drill.Grade.WRONG, "category": "basics"},
    ]
    meter_basic_miss = drill.burn_meter(items2)
    assert meter_basic_miss > meter_anchor_miss


def test_burn_meter_empty():
    assert drill.burn_meter([]) == 0


def test_weakest_items():
    ident = _ident()
    answers = {i.prompt: i.answer for i in drill.build_drill(ident)}
    # Miss exactly one item.
    target = drill.build_drill(ident)[0].prompt
    result = drill.run_drill(ident, lambda p: "wrong" if p == target else answers[p])
    weakest = drill.weakest_items(result, n=1)
    assert weakest[0]["prompt"] == target
    assert weakest[0]["grade"] == drill.Grade.WRONG
