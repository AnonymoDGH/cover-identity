"""Tests for cover_identity.burn -- compromise response planning."""

from __future__ import annotations

import pytest

from cover_identity import burn


def test_default_plan_starts_at_lay_low():
    plan = burn.default_plan()
    assert plan.current.name == "lay-low"
    assert plan.index == 0


def test_level_names():
    plan = burn.default_plan()
    assert plan.level_names() == ["lay-low", "soft-freeze",
                                  "hard-freeze", "evacuate"]


def test_escalate_moves_up():
    plan = burn.default_plan()
    level = plan.escalate()
    assert level.name == "soft-freeze"
    assert plan.index == 1


def test_escalate_multiple_steps():
    plan = burn.default_plan()
    level = plan.escalate(steps=3)
    assert level.name == "evacuate"


def test_escalate_caps_at_top():
    plan = burn.default_plan()
    plan.escalate(steps=99)
    assert plan.current.name == "evacuate"
    assert plan.index == len(burn.LEVELS) - 1


def test_escalate_invalid_steps():
    plan = burn.default_plan()
    with pytest.raises(burn.BurnError):
        plan.escalate(steps=0)


def test_reset_returns_to_mild():
    plan = burn.default_plan()
    plan.escalate(steps=2)
    plan.reset()
    assert plan.current.name == "lay-low"


def test_actions_at_named_level():
    plan = burn.default_plan()
    actions = plan.actions_at("evacuate")
    assert any("route" in a for a in actions)


def test_actions_at_unknown_level_raises():
    plan = burn.default_plan()
    with pytest.raises(burn.BurnError):
        plan.actions_at("nonexistent")


def test_cumulative_destroy_grows():
    plan = burn.default_plan()
    assert plan.cumulative_destroy() == []  # lay-low destroys nothing
    plan.escalate()
    soft = plan.cumulative_destroy()
    assert soft
    plan.escalate()
    hard = plan.cumulative_destroy()
    assert len(hard) > len(soft)


def test_to_dict_shape():
    plan = burn.default_plan()
    plan.escalate()
    d = plan.to_dict()
    assert d["current"] == "soft-freeze"
    assert d["current_index"] == 1
    assert len(d["levels"]) == len(burn.LEVELS)
    assert d["levels"][0]["name"] == "lay-low"


def test_empty_levels_rejected():
    with pytest.raises(burn.BurnError):
        burn.BurnPlan(levels=[])


def test_every_level_has_trigger_and_actions():
    for level in burn.LEVELS:
        assert level.trigger
        assert level.actions
