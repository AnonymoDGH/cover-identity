"""Tests for cover_identity.appearance -- description and disguise."""

from __future__ import annotations

import random

import pytest

from cover_identity import appearance as ap


def test_build_description_deterministic():
    a = ap.build_description(random.Random(1), 40)
    b = ap.build_description(random.Random(1), 40)
    assert a == b


def test_build_description_shape():
    d = ap.build_description(random.Random(2), 35)
    assert 158 <= d.height_cm <= 196
    assert d.build in ap._BUILDS
    assert d.distinguishing


def test_build_description_older_gets_grey_hair():
    d = ap.build_description(random.Random(3), 60)
    assert d.hair in {"grey", "grey-streaked", "salt-and-pepper", "thinning"}


def test_build_description_negative_age():
    with pytest.raises(ap.AppearanceError):
        ap.build_description(random.Random(1), -1)


def test_description_to_text():
    d = ap.build_description(random.Random(4), 30)
    text = d.to_text()
    assert "cm" in text
    assert d.build in text


def test_disguise_item_rejects_nonpositive_seconds():
    with pytest.raises(ap.AppearanceError):
        ap.DisguiseItem("x", "head", 0, "nope")


def test_wardrobe_wraps_weekly():
    w = ap.Wardrobe(random.Random(1), days=7)
    assert w.outfit_for_day(0) == w.outfit_for_day(7)
    assert len(w) == 7


def test_wardrobe_rejects_zero_days():
    with pytest.raises(ap.AppearanceError):
        ap.Wardrobe(random.Random(1), days=0)


def test_kit_apply_and_applied():
    kit = ap.DisguiseKit()
    kit.apply("knit cap")
    assert [i.name for i in kit.applied()] == ["knit cap"]


def test_kit_apply_unknown_raises():
    kit = ap.DisguiseKit()
    with pytest.raises(ap.AppearanceError):
        kit.apply("invisible cloak")


def test_kit_same_slot_replaces():
    kit = ap.DisguiseKit()
    kit.apply("knit cap")
    kit.apply("baseball cap")  # same slot: head
    names = [i.name for i in kit.applied()]
    assert names == ["baseball cap"]


def test_kit_remove():
    kit = ap.DisguiseKit()
    kit.apply("knit cap")
    kit.remove("knit cap")
    assert kit.applied() == []


def test_kit_remove_not_applied_raises():
    kit = ap.DisguiseKit()
    with pytest.raises(ap.AppearanceError):
        kit.remove("knit cap")


def test_kit_change_seconds():
    kit = ap.DisguiseKit()
    kit.apply("knit cap")       # 5s
    kit.apply("clear-lens glasses")  # 3s
    assert kit.change_seconds() == 8


def test_kit_slots_covered():
    kit = ap.DisguiseKit()
    kit.apply("knit cap")
    kit.apply("loose work jacket")
    assert kit.slots_covered() == ["head", "torso"]


def test_kit_available_sorted():
    kit = ap.DisguiseKit()
    assert kit.available() == sorted(kit.available())
    assert "knit cap" in kit.available()
