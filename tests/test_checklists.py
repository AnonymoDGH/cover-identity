"""Tests for cover_identity.checklists -- pre-action checklists."""

from __future__ import annotations

import pytest

from cover_identity import checklists as cl


def test_get_known_checklists():
    for name in cl.CHECKLISTS:
        checklist = cl.get_checklist(name)
        assert checklist.name == name
        assert len(checklist) >= 1


def test_get_unknown_raises():
    with pytest.raises(cl.ChecklistError):
        cl.get_checklist("nonexistent")


def test_starts_unchecked():
    checklist = cl.get_checklist("pre-meeting")
    assert not checklist.is_done(0)
    assert checklist.progress()["done"] == 0


def test_check_and_uncheck():
    checklist = cl.get_checklist("pre-meeting")
    checklist.check(0)
    assert checklist.is_done(0)
    checklist.uncheck(0)
    assert not checklist.is_done(0)


def test_check_out_of_range():
    checklist = cl.get_checklist("pre-meeting")
    with pytest.raises(cl.ChecklistError):
        checklist.check(99)


def test_ready_requires_required_only():
    checklist = cl.get_checklist("pre-meeting")
    # Check only the required items.
    for i in range(len(checklist)):
        if checklist.item(i).required:
            checklist.check(i)
    assert checklist.ready() is True


def test_not_ready_when_required_missing():
    checklist = cl.get_checklist("pre-meeting")
    assert checklist.ready() is False
    missing = checklist.missing_required()
    assert missing  # at least one required item unchecked


def test_missing_required_empty_when_done():
    checklist = cl.get_checklist("pre-travel")
    for i in range(len(checklist)):
        if checklist.item(i).required:
            checklist.check(i)
    assert checklist.missing_required() == []


def test_progress_complete():
    checklist = cl.get_checklist("post-incident")
    for i in range(len(checklist)):
        checklist.check(i)
    progress = checklist.progress()
    assert progress["complete"] is True
    assert progress["done"] == progress["total"]


def test_to_text_marks():
    checklist = cl.get_checklist("pre-meeting")
    checklist.check(0)
    text = checklist.to_text()
    assert "[x]" in text
    assert "[ ]" in text
    assert "CHECKLIST: pre-meeting" in text


def test_empty_checklist_rejected():
    with pytest.raises(cl.ChecklistError):
        cl.Checklist(name="x", purpose="y", items=[])


def test_every_item_has_why():
    for name in cl.CHECKLISTS:
        checklist = cl.get_checklist(name)
        for i in range(len(checklist)):
            assert checklist.item(i).why
