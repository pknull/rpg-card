"""Lifecycle and subclass regressions not covered by the named fixtures."""

import random

import pytest

from card_picker import BaseCard, Deck, Hand, StandardCard


def test_custom_two_argument_card_constructor_still_supported():
    class CustomCard(StandardCard):
        def __init__(self, suit, number):
            super().__init__(suit, number)

    deck = Deck(CustomCard)
    deck.create()
    assert len(deck) == 54
    assert deck.deal(ncards=1) == ["King of Clubs"]


def test_custom_major_only_system_without_suit_labels_still_supported():
    class Omens(BaseCard):
        MAJOR_NUMBERS = ["Sun", "Moon"]

    deck = Deck(Omens)
    deck.create()
    assert deck.deal(2) == ["Moon", "Sun"]


@pytest.mark.parametrize("deck,size", [
    (Deck.standard(jokers=False), 52),
    (Deck.tarot(arcana="major"), 22),
    (Deck.tarot(arcana="minor"), 56),
])
def test_create_retains_builder_configuration_and_clears_hands(deck, size):
    hand = Hand(deck)
    old = hand.draw(3)
    cards_list = deck.cards
    deck.create()
    assert len(deck) == size
    assert deck.cards is cards_list
    assert hand.cards == []
    assert not set(old) & set(deck.cards)
    assert len(Deck.from_cards(old)) == 3


def test_seeded_all_card_recall_is_reproducible():
    def signature(deck):
        return [(c.suit, c.number, c.orientation) for c in deck.cards]

    first, second = Deck.standard(seed=19), Deck.standard(seed=19)
    for deck in (first, second):
        deck.shuffle()
        hand = Hand(deck)
        hand.draw(6)
        deck.discard(hand.cards[:2])
        deck.deal(4)
        deck.reshuffle(all_cards=True)
        assert hand.cards == []
    assert signature(first) == signature(second)


def test_invalid_reshuffle_preserves_zones_hands_and_rng():
    rng = random.Random(9)
    deck = Deck.standard(rng=rng)
    hand = Hand(deck)
    hand.draw(4)
    hand.discard(hand.cards[:2])
    before = list(deck.cards), list(deck.discards), list(hand.cards), rng.getstate()
    with pytest.raises(ValueError):
        deck.reshuffle(all_cards=True, upright_count=55)
    assert (deck.cards, deck.discards, hand.cards, rng.getstate()) == before


def test_mixed_detached_and_drawn_return_batch():
    deck = Deck.standard()
    card = deck.draw()[0]
    detached = StandardCard(1, 0)
    deck.return_cards([card, detached])
    assert deck.draw(2) == [card, detached]
    with pytest.raises(ValueError):
        Deck.from_cards([detached])


def test_compose_invalid_seed_or_duplicate_source_is_atomic():
    first, second = Deck.standard(), Deck.standard()
    before = list(first.cards), list(second.cards)
    with pytest.raises(ValueError):
        Deck.combine(first, second, seed=1, rng=random.Random(1))
    assert (first.cards, second.cards) == before
    with pytest.raises(ValueError):
        Deck.combine(first, first)
    assert (first.cards, second.cards) == before


def test_hand_foreign_play_and_discard_are_atomic():
    deck = Deck.standard()
    first, second = Hand(deck), Hand(deck)
    left, right = first.draw(2), second.draw(2)
    with pytest.raises(ValueError):
        first.discard([left[0], right[0]])
    assert first.cards == left
    assert second.cards == right
    assert deck.discards == []
    with pytest.raises(ValueError):
        first.play(right[0])
    deck.return_cards(left)
    assert first.cards == []
