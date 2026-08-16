"""Tests for cover_identity.network -- the cover's social web."""

from __future__ import annotations

from cover_identity import network as net


def test_network_deterministic():
    a = net.build_network(seed=3, size=5)
    b = net.build_network(seed=3, size=5)
    assert a == b


def test_network_size():
    for size in (1, 3, 7):
        assert len(net.build_network(seed=1, size=size)) == size


def test_network_has_at_most_one_old_friend():
    network = net.build_network(seed=9, size=8)
    deep = [c for c in network if c["relationship"] == "old friend"]
    assert len(deep) <= 1


def test_closeness_within_relationship_bounds():
    network = net.build_network(seed=2, size=10)
    for c in network:
        lo, hi = net.RELATIONSHIPS[c["relationship"]]
        assert lo <= c["closeness"] <= hi


def test_make_contact_explicit_relationship():
    import random
    c = net.make_contact(random.Random(1), "landlord")
    assert c["relationship"] == "landlord"
    assert c["context"]


def test_vouch_list_filters_by_threshold():
    network = [
        {"name": "A", "closeness": 0.9},
        {"name": "B", "closeness": 0.3},
        {"name": "C", "closeness": 0.5},
    ]
    vouch = net.vouch_list(network, threshold=0.5)
    assert {c["name"] for c in vouch} == {"A", "C"}


def test_network_to_text_sorted_by_closeness():
    network = net.build_network(seed=4, size=5)
    text = net.network_to_text(network)
    lines = [ln for ln in text.splitlines() if ln.startswith("- ")]
    assert len(lines) == 5


def test_invalid_size_raises():
    import pytest
    with pytest.raises(ValueError):
        net.build_network(seed=1, size=0)
