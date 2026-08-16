"""Tests for cover_identity.habits -- daily routine and habits."""

from __future__ import annotations

import random

import pytest

from cover_identity import habits as hb


def test_build_routine_deterministic():
    a = hb.build_routine(random.Random(1), "locksmith")
    b = hb.build_routine(random.Random(1), "locksmith")
    assert a == b


def test_routine_contiguous_no_gaps():
    blocks = hb.build_routine(random.Random(2), "archivist")
    for prev, nxt in zip(blocks, blocks[1:]):
        assert prev.end_hour == nxt.start_hour


def test_routine_mentions_occupation():
    blocks = hb.build_routine(random.Random(3), "locksmith")
    joined = " ".join(b.activity for b in blocks)
    assert "locksmith" in joined


def test_routine_covers_working_hours():
    blocks = hb.build_routine(random.Random(4), "translator")
    assert hb.where_at(blocks, 10) is not None
    assert hb.where_at(blocks, 14) is not None


def test_where_at_outside_range():
    blocks = hb.build_routine(random.Random(5), "clerk")
    assert hb.where_at(blocks, 3) is None  # asleep


def test_where_at_invalid_hour():
    blocks = hb.build_routine(random.Random(6), "clerk")
    with pytest.raises(hb.HabitsError):
        hb.where_at(blocks, 25)


def test_build_habits_shape():
    h = hb.build_habits(random.Random(7))
    assert h.coffee_order in hb._COFFEES
    assert h.reads in hb._PAPERS
    assert h.walk in hb._WALKS
    assert len(h.to_list()) == 5


def test_habits_deterministic():
    a = hb.build_habits(random.Random(8))
    b = hb.build_habits(random.Random(8))
    assert a == b


def test_routine_to_text():
    blocks = hb.build_routine(random.Random(9), "baker")
    text = hb.routine_to_text(blocks)
    assert "DAILY ROUTINE" in text
    assert "baker" in text


def test_block_covers():
    block = hb.RoutineBlock(9, 12, "work", "office")
    assert block.covers(9) and block.covers(11)
    assert not block.covers(12) and not block.covers(8)
