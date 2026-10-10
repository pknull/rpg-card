"""Card attributes, deck state, identity, orientation, and hand contracts."""

from fractions import Fraction
import random

import pytest

import card_picker as cp


def signature(deck):
    return [(type(c).__name__, c.suit, c.number, c.orientation) for c in deck.cards]


@pytest.mark.parametrize('cls,suit,rank,value,colour,arcana', [
    (cp.StandardCard, 1, 0, 1, 'red', None),
    (cp.StandardCard, 2, 12, 13, 'black', None),
    (cp.StandardCard, 3, 10, 11, 'red', None),
    (cp.StandardCard, 4, 11, 12, 'black', None),
    (cp.StandardCard, 0, 1, 0, None, None),
    (cp.TarotCard, 0, 10, 10, None, 'major'),
    (cp.TarotCard, 2, 10, 11, None, 'minor'),
    (cp.TarotCard, 4, 13, 14, None, 'minor'),
    (cp.ShadowCard, 0, 0, 0, None, 'major'),
    (cp.ShadowCard, 1, 11, 12, None, 'minor'),
    (cp.UnoCard, 1, 0, 0, None, None),
    (cp.UnoCard, 2, 4, 1, None, None),
    (cp.UnoCard, 3, 12, 9, None, None),
    (cp.UnoCard, 4, 13, 1, None, None),
    (cp.UnoCard, 1, 21, 9, None, None),
    (cp.UnoCard, 1, 2, 0, None, None),
    (cp.UnoCard, 0, 7, 0, None, None),
])
def test_structured_attributes(cls, suit, rank, value, colour, arcana):
    """Fails if attributes are absent or inferred from ambiguous display names."""
    card = cls(suit, rank)
    assert (card.suit, card.number, card.rank_index) == (suit, rank, rank)
    assert (card.value, card.colour, card.arcana) == (value, colour, arcana)
    assert card.orientation == 'upright'


def test_value_mapping_precedence_and_exact_fraction_values():
    """Fails if configurable values ignore suit-specific overrides or change names."""
    deck = cp.Deck.standard(jokers=False, value_map={0: 14, (1, 0): Fraction(29, 2)})
    aces = {c.suit: c for c in deck.cards if c.rank_index == 0}
    assert aces[1].value == Fraction(29, 2)
    assert aces[2].value == aces[3].value == aces[4].value == 14
    assert aces[1].name() == 'Ace of Hearts'
    assert cp.TarotCard(4, 13, value_map={13: 20}).value == 20


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), 1.5, 'ace'])
def test_invalid_numeric_mapping_is_rejected(value):
    """Fails if exact-value configuration admits non-rational or boolean values."""
    assert cp.StandardCard(1, 0, value_map={0: 14}).value == 14
    with pytest.raises((TypeError, ValueError)):
        cp.StandardCard(1, 0, value_map={0: value})


@pytest.mark.parametrize('builder,kwargs,size', [
    ('standard', {}, 54), ('standard', {'jokers': False}, 52),
    ('tarot', {}, 78), ('tarot', {'arcana': 'major'}, 22),
    ('tarot', {'arcana': 'minor'}, 56), ('shadow', {}, 78), ('uno', {}, 96),
])
def test_populated_builders(builder, kwargs, size):
    """Fails if builders omit requested cards or silently change legacy composition."""
    deck = getattr(cp.Deck, builder)(**kwargs)
    assert len(deck) == size
    assert len({id(c) for c in deck.cards}) == size
    if 'arcana' in kwargs:
        assert {c.arcana for c in deck.cards} == {kwargs['arcana']}


def test_create_resets_all_zones_and_detaches_old_cards():
    """Fails if create retains discards or leaves old cards attached to the reset deck."""
    deck = cp.Deck(cp.StandardCard)
    deck.create()
    old = deck.draw(2)
    deck.discard(old[:1])
    deck.create()
    assert len(deck) == 54
    assert deck.discards == []
    assert not set(old) & set(deck.cards)
    adopted = cp.Deck.from_cards(old)
    assert adopted.draw(2) == old[::-1]


def test_draw_peek_and_exhaustion_are_atomic():
    """Fails if peek consumes cards or a failed draw partially depletes the pile."""
    deck = cp.Deck.standard(jokers=False)
    expected = deck.peek(3)
    assert len(deck) == 52
    assert [c.name() for c in expected] == ['King of Clubs', 'Queen of Clubs', 'Jack of Clubs']
    assert deck.draw(3) == expected
    remaining = list(deck.cards)
    with pytest.raises(cp.DeckExhausted):
        deck.draw(50)
    assert deck.cards == remaining
    assert deck.peek(100) == list(reversed(remaining))
    assert deck.draw(0) == []
    assert deck.peek(0) == []
    deck.draw(49)
    with pytest.raises(cp.DeckExhausted):
        deck.draw()
    assert deck.deal(10) == []


@pytest.mark.parametrize('method', ['draw', 'peek'])
@pytest.mark.parametrize('n', [-1, 1.5, True, '2'])
def test_invalid_draw_and_peek_sizes_are_atomic(method, n):
    """Fails if invalid counts coerce or consume a partial sample."""
    deck = cp.Deck.standard()
    before = list(deck.cards)
    with pytest.raises((TypeError, ValueError)):
        getattr(deck, method)(n)
    assert deck.cards == before


def test_discard_return_and_bottom_order_preserve_physical_identity():
    """Fails if discard or return copies cards, duplicates them, or reverses top order."""
    deck = cp.Deck.standard()
    drawn = deck.draw(3)
    deck.discard(drawn[:2])
    assert deck.discards == drawn[:2]
    deck.return_cards(drawn, top=True)
    assert deck.discards == []
    assert deck.draw(3) == drawn
    deck.return_cards(drawn, top=False)
    deck.draw(51)
    assert deck.draw(3) == drawn


def test_invalid_zone_transfers_are_atomic():
    """Fails if transfers accept foreign/duplicate cards or partially apply invalid batches."""
    deck = cp.Deck.standard()
    drawn = deck.draw(2)
    foreign = cp.StandardCard(1, 0)
    other = cp.Deck.from_cards([foreign])
    for batch in ([drawn[0], foreign], [drawn[0], drawn[0]], [deck.cards[0]]):
        before = list(deck.cards)
        with pytest.raises(ValueError):
            deck.discard(batch)
        assert deck.cards == before
        assert deck.discards == []
        with pytest.raises(ValueError):
            deck.return_cards(batch)
        assert deck.cards == before
    assert other.cards == [foreign]
    deck.discard(drawn)
    with pytest.raises(ValueError):
        deck.discard(drawn)


def test_reshuffle_discards_then_all_cards():
    """Fails if normal reshuffle recalls held cards or all-card reshuffle leaves them out."""
    deck = cp.Deck.standard(seed=81)
    original = set(deck.cards)
    held = deck.draw(5)
    deck.discard(held[:2])
    deck.reshuffle(upright_count=10)
    assert len(deck) == 51
    assert deck.discards == []
    assert not set(held[2:]) & set(deck.cards)
    deck.reshuffle(all_cards=True, upright_count=20)
    assert set(deck.cards) == original
    assert sum(c.orientation == 'upright' for c in deck.cards) == 20
    with pytest.raises(ValueError):
        deck.return_cards(held[2:])


def test_draw_until_includes_match_and_consumes_remainder_on_failure():
    """Fails if draw_until omits its matching card or silently succeeds without a match."""
    deck = cp.Deck.standard(jokers=False)
    result = deck.draw_until(lambda c: c.rank_index == 10)
    assert [c.rank_index for c in result] == [12, 11, 10]
    with pytest.raises(cp.DeckExhausted):
        deck.draw_until(lambda c: c.suit == 0)
    assert len(deck) == 0
    deck.reshuffle(all_cards=True)
    assert len(deck) == 52


def test_orientation_fixed_counts_probability_extremes_and_persistence():
    """Fails if orientation is resampled on draw/return rather than at shuffle."""
    deck = cp.Deck.tarot(arcana='major', seed=9)
    deck.shuffle(upright_count=11)
    assert sum(c.orientation == 'upright' for c in deck.cards) == 11
    original = {id(c): c.orientation for c in deck.cards}
    cards = deck.draw(4)
    deck.discard(cards)
    deck.return_cards(cards)
    assert {id(c): c.orientation for c in deck.cards} == original
    deck.shuffle(upright_probability=0)
    assert {c.orientation for c in deck.cards} == {'reversed'}
    deck.shuffle(upright_probability=1)
    assert {c.orientation for c in deck.cards} == {'upright'}


@pytest.mark.parametrize('kwargs', [
    {'upright_probability': -0.1}, {'upright_probability': 1.1},
    {'upright_probability': float('nan')}, {'upright_probability': float('inf')},
    {'upright_count': -1}, {'upright_count': 55}, {'upright_count': 1.5}, {'upright_count': True},
])
def test_invalid_shuffle_is_atomic_including_rng(kwargs):
    """Fails if shuffle validates after moving cards or consuming random numbers."""
    rng = random.Random(789)
    deck = cp.Deck.standard(rng=rng)
    before = signature(deck), rng.getstate()
    with pytest.raises((TypeError, ValueError)):
        deck.shuffle(**kwargs)
    assert (signature(deck), rng.getstate()) == before


def test_seed_rng_and_module_random_reproducibility():
    """Fails if shuffle ignores injected RNGs or legacy module random.seed calls."""
    seeded = cp.Deck.standard(seed=412)
    supplied = cp.Deck.standard(rng=random.Random(412))
    seeded.shuffle()
    supplied.shuffle()
    assert signature(seeded) == signature(supplied)
    random.seed(992)
    first = cp.Deck.standard()
    first.shuffle()
    random.seed(992)
    second = cp.Deck.standard()
    second.shuffle()
    assert signature(first) == signature(second)
    with pytest.raises(ValueError):
        cp.Deck(cp.StandardCard, seed=412, rng=random.Random(412))


def test_remove_intersection_detaches_cards_from_future_recall():
    """Fails if remove unions selectors or all-card reshuffle restores excluded cards."""
    deck = cp.Deck.tarot()
    removed = deck.remove(suit=1, rank=0, arcana='minor')
    assert [c.name() for c in removed] == ['Ace of Swords']
    assert len(deck) == 77
    deck.reshuffle(all_cards=True)
    assert not set(removed) & set(deck.cards)
    new = cp.Deck.from_cards(removed)
    assert new.draw() == removed


def test_combine_moves_remaining_cards_only():
    """Fails if combining aliases ownership or recalls source drawn/discarded cards."""
    left, right = cp.Deck.standard(), cp.Deck.standard()
    drawn = left.draw(2)
    left.discard(drawn[:1])
    expected = set(left.cards + right.cards)
    joined = cp.Deck.combine(left, right)
    assert set(joined.cards) == expected
    assert len(joined) == 106
    assert len(left) == len(right) == 0
    assert left.discards == drawn[:1]
    left.reshuffle(all_cards=True)
    assert set(left.cards) == set(drawn)
    assert not set(left.cards) & set(joined.cards)


def test_split_is_exclusive_atomic_and_transfers_remaining_cards():
    """Fails if split duplicates, drops, or retains ownership of partitioned cards."""
    deck = cp.Deck.tarot()
    before = list(deck.cards)
    for invalid in ({'all': lambda c: True, 'also_all': lambda c: True}, {'major': lambda c: c.arcana == 'major'}):
        with pytest.raises(ValueError):
            deck.split(invalid)
        assert deck.cards == before
    piles = deck.split({'major': lambda c: c.arcana == 'major', 'minor': lambda c: c.arcana == 'minor'})
    assert len(piles['major']) == 22
    assert len(piles['minor']) == 56
    assert len(deck) == 0
    deck.reshuffle(all_cards=True)
    assert len(deck) == 0
    assert set(piles['major'].cards + piles['minor'].cards) == set(before)


def test_from_cards_rejects_duplicate_physical_cards_and_foreign_ownership():
    """Fails if one physical card can be present twice or in two decks."""
    card = cp.StandardCard(1, 0)
    with pytest.raises(ValueError):
        cp.Deck.from_cards([card, card])
    deck = cp.Deck.from_cards([card])
    with pytest.raises(ValueError):
        cp.Deck.from_cards(deck.cards)


def test_hand_draw_play_discard_and_recall():
    """Fails if hand operations lose cards or retained hand references survive recall."""
    deck = cp.Deck.tarot(arcana='major', seed=33)
    hand = cp.Hand(deck)
    drawn = hand.draw(3)
    assert hand.cards == drawn
    assert len(deck) == 19
    assert hand.play(drawn[0]) is drawn[0]
    assert hand.cards == drawn[1:]
    hand.discard(drawn[1:2])
    assert deck.discards == drawn[1:2]
    assert hand.cards == drawn[2:]
    deck.reshuffle(all_cards=True)
    assert hand.cards == []
    with pytest.raises(ValueError):
        hand.play(drawn[2])
    assert len(deck) == 22
