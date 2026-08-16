"""Tests for cover_identity.speech -- verbal camouflage."""

from __future__ import annotations

import random

from cover_identity import generate
from cover_identity import speech


def _kit():
    ident = generate(seed=42)
    return speech.build_speech_kit(random.Random(1), ident), ident


def test_build_speech_kit_shape():
    kit, ident = _kit()
    assert len(kit["fillers"]) == 3
    assert len(kit["deflections"]) == 3
    assert len(kit["safe_topics"]) == 4
    assert kit["danger_topics"]
    assert kit["never_say"] == speech.NEVER_SAY


def test_speech_kit_deterministic():
    ident = generate(seed=42)
    a = speech.build_speech_kit(random.Random(1), ident)
    b = speech.build_speech_kit(random.Random(1), ident)
    assert a == b


def test_safe_topics_reference_hobbies_or_job():
    kit, ident = _kit()
    joined = " ".join(kit["safe_topics"])
    assert ident["occupation"] in joined


def test_steer_topics_on_danger():
    kit, _ = _kit()
    reply = speech.steer_topics(kit, "what do you think about politics?")
    assert reply == kit["safe_topics"][0]


def test_steer_topics_neutral_deflects():
    kit, _ = _kit()
    reply = speech.steer_topics(kit, "do you like coffee?")
    assert reply == kit["deflections"][0]


def test_score_leakage_clean():
    result = speech.score_leakage("I had a quiet day, mostly reading.")
    assert result["match_count"] == 0
    assert result["score"] == 0.0


def test_score_leakage_detects_forbidden():
    result = speech.score_leakage("Well, my handler said the agency is fine.")
    assert "my handler" in result["matches"]
    assert "the agency" in result["matches"]
    assert result["match_count"] == 2
    assert result["score"] > 0.5


def test_score_leakage_hedge_density():
    hedgy = "um maybe perhaps I guess um uh maybe perhaps I guess"
    result = speech.score_leakage(hedgy)
    assert result["hedges"] > 0
    assert result["score"] > 0


def test_score_leakage_custom_list():
    result = speech.score_leakage("the word badger appears",
                                  never_say=["badger"])
    assert result["matches"] == ["badger"]


def test_speech_report_clean():
    kit, _ = _kit()
    report = speech.speech_report(kit, "a perfectly ordinary sentence.")
    assert report["clean"] is True
    assert report["verdict"] == "clean"


def test_speech_report_burn():
    kit, _ = _kit()
    report = speech.speech_report(
        kit, "my handler and the agency and my real name and classified")
    assert report["clean"] is False
    assert report["verdict"] == "burn"
