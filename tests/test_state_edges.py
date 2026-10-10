"""Regression probes for the independently reviewed serialization boundaries."""

import sys

import pytest

from card_picker import Deck, SnapshotError, restore, snapshot


@pytest.mark.parametrize("system,suit,rank", [
    ("standard", None, 13), ("standard", 0, 2),
    ("standard", 5, 0), ("tarot", None, 22),
    ("tarot", 1, 14), ("uno", 0, 8),
])
def test_restore_rejects_override_indices_outside_full_card_system(system, suit, rank):
    deck = getattr(Deck, system)(seed=1)
    state = snapshot(deck)
    state["deck"]["value_map"] = [{"suit": suit, "rank": rank, "value": [1, 1]}]
    with pytest.raises(SnapshotError, match="mapped (rank|suit)"):
        restore(state)


def test_collision_heavy_integer_map_rejected_before_dictionary_construction():
    state = snapshot(Deck.standard(seed=1))
    state["deck"]["value_map"] = [
        {"suit": None, "rank": i * sys.hash_info.modulus, "value": [1, 1]}
        for i in range(10_000)
    ]
    with pytest.raises(SnapshotError, match="mapped rank"):
        restore(state)


def test_snapshot_rejects_unused_invalid_indices_in_live_recipe():
    deck = Deck.standard(value_map={13: 99})
    with pytest.raises(SnapshotError, match="mapped rank"):
        snapshot(deck)


def test_valid_overrides_survive_when_cards_are_absent_from_selection():
    deck = Deck.tarot(arcana="major", value_map={(1, 13): 99, 21: 77})
    state = snapshot(deck)
    restored, _ = restore(state)
    assert snapshot(restored) == state
    restored.create()
    assert next(c for c in restored.cards if c.number == 21).value == 77


@pytest.mark.parametrize("key", [(None, 0), (True, 0), (1, None)])
def test_snapshot_does_not_reinterpret_malformed_live_tuple_keys(key):
    deck = Deck.standard(seed=1)
    deck._value_map = {key: 99}
    before = list(deck.cards), deck._rng.getstate()
    with pytest.raises(SnapshotError):
        snapshot(deck)
    assert (deck.cards, deck._rng.getstate()) == before
    assert deck._value_map == {key: 99}
