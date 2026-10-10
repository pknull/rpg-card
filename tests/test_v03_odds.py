"""Exact acceptance fixtures from the approved 2026-10-09 requirements."""

from collections import Counter
from fractions import Fraction
from itertools import permutations, product
import math
import random

import pytest

import card_picker as cp


def mass(distribution, predicate):
    return sum((p for outcome, p in distribution.items() if predicate(outcome)), Fraction())


def assert_distribution(distribution):
    assert distribution
    assert all(isinstance(p, Fraction) and p > 0 for p in distribution.values())
    assert sum(distribution.values()) == 1


def small_deck():
    # Physical cards have duplicate values but remain distinguishable.
    return cp.Deck.from_cards([
        cp.StandardCard(1, 0), cp.StandardCard(2, 0),
        cp.StandardCard(1, 2), cp.StandardCard(4, 4),
    ])


def brute_distribution(values, n, replacement, reading):
    samples = product(range(len(values)), repeat=n) if replacement else permutations(range(len(values)), n)
    counts = Counter(reading([values[i] for i in sample]) for sample in samples)
    total = sum(counts.values())
    return {value: Fraction(count, total) for value, count in counts.items()}


def test_document_ace_and_joker_fixtures():
    """Fails if exact count odds omit multiplicity or use replacement by default."""
    aces = cp.Odds(cp.Deck.standard(jokers=False)).count(5, lambda c: c.rank_index == 0)
    jokers = cp.Odds(cp.Deck.standard()).count(10, lambda c: c.suit == 0)
    assert mass(aces, lambda n: n >= 1) == Fraction(18472, 54145)
    assert mass(jokers, lambda n: n >= 1) == Fraction(485, 1431)


def test_document_major_fixture_uses_attributes_not_names():
    """Fails if Wheel of Fortune is misclassified by parsing its name."""
    dist = cp.Odds(cp.Deck.tarot()).count(3, lambda c: c.arcana == 'major')
    assert mass(dist, lambda n: n >= 1) == Fraction(157, 247)


def test_document_dependent_high_card_fixture():
    """Fails if same-deck comparison is incorrectly treated as independent."""
    deck = cp.Deck.standard(jokers=False)
    expected = {'win': Fraction(8, 17), 'tie': Fraction(1, 17), 'loss': Fraction(8, 17)}
    assert cp.Odds(deck).compare() == expected
    assert cp.Odds(deck).compare(other=deck) == expected


def test_document_highest_and_lowest_fixtures():
    """Fails if order statistics count ordered outcomes with the wrong weights."""
    odds = cp.Odds(cp.Deck.standard(jokers=False))
    assert mass(odds.reading(2, kind='highest'), lambda v: v >= 10) == Fraction(116, 221)
    assert mass(odds.reading(2, kind='lowest'), lambda v: v >= 10) == Fraction(20, 221)


def test_document_joint_suit_fixtures():
    """Fails if joint counts ignore dependence between suit categories."""
    odds = cp.Odds(cp.Deck.standard(jokers=False))
    predicates = [lambda c, s=s: c.suit == s for s in range(1, 5)]
    assert mass(odds.counts(3, predicates), lambda counts: max(counts) >= 2) == Fraction(256, 425)
    assert mass(odds.counts(5, predicates), lambda counts: min(counts) >= 1) == Fraction(2197, 8330)


def test_document_orientation_fixture():
    """Fails if fixed-count orientation is not visible to exact predicates."""
    deck = cp.Deck.tarot(arcana='major', seed=104)
    deck.shuffle(upright_count=11)
    assert cp.Odds(deck).count(3, lambda c: c.orientation == 'upright')[3] == Fraction(3, 28)


def test_document_remaining_hearts_fixture():
    """Fails if exact odds use the original deck rather than remaining cards."""
    deck = cp.Deck.standard(jokers=False)
    cards = deck.draw(52)
    hearts = [c for c in cards if c.suit == 1]
    others = [c for c in cards if c.suit != 1]
    deck.return_cards(hearts + others, top=True)
    assert all(c.suit == 1 for c in deck.draw(3))
    assert cp.Odds(deck).count(1, lambda c: c.suit == 1)[1] == Fraction(10, 49)


@pytest.mark.parametrize('replacement', [False, True])
@pytest.mark.parametrize('kind,k,reading', [
    ('sum', None, sum), ('highest', None, max), ('lowest', None, min),
    ('kth', 2, lambda vs: sorted(vs)[1]),
])
def test_readings_match_physical_card_enumeration(replacement, kind, k, reading):
    """Fails if duplicate numeric values lose physical-card multiplicity."""
    kwargs = {'k': k} if k is not None else {}
    actual = cp.Odds(small_deck()).reading(3, kind=kind, replacement=replacement, **kwargs)
    assert actual == brute_distribution([1, 1, 3, 5], 3, replacement, reading)
    assert_distribution(actual)


@pytest.mark.parametrize('replacement', [False, True])
def test_overlapping_predicates_match_enumeration(replacement):
    """Fails if multivariate counts incorrectly require disjoint predicates."""
    deck = small_deck()
    predicates = [lambda c: c.suit == 1, lambda c: c.value == 1]
    actual = cp.Odds(deck).counts(3, predicates, replacement=replacement)
    signatures = [(1, 1), (0, 1), (1, 0), (0, 0)]
    expected = brute_distribution(signatures, 3, replacement, lambda vs: tuple(map(sum, zip(*vs))))
    assert actual == expected
    assert_distribution(actual)


def test_reading_count_and_custom_value_functions():
    """Fails if reading ignores predicate or custom numeric values."""
    odds = cp.Odds(small_deck())
    predicate = lambda c: c.value == 1
    assert odds.reading(2, kind='count', predicate=predicate) == {0: Fraction(1, 6), 1: Fraction(2, 3), 2: Fraction(1, 6)}
    assert odds.reading(1, value=lambda c: -c.value) == {-1: Fraction(1, 2), -3: Fraction(1, 4), -5: Fraction(1, 4)}


@pytest.mark.parametrize('replacement', [False, True])
def test_dependent_multicard_comparison_matches_enumeration(replacement):
    """Fails if the second dependent draw forgets cards consumed by the first."""
    values = [1, 1, 3, 5]
    samples = product(range(4), repeat=4) if replacement else permutations(range(4), 4)
    counts = Counter()
    for sample in samples:
        left = max(values[i] for i in sample[:2])
        right = sum(values[i] for i in sample[2:])
        counts['win' if left > right else 'tie' if left == right else 'loss'] += 1
    total = sum(counts.values())
    expected = {key: Fraction(counts[key], total) for key in ('win', 'tie', 'loss')}
    assert cp.Odds(small_deck()).compare(2, other_n=2, kind='highest', other_kind='sum', replacement=replacement) == expected


def test_independent_comparison_and_custom_values():
    """Fails if separate decks are depleted jointly or value callbacks ignored."""
    left = small_deck()
    right = cp.Deck.from_cards([cp.StandardCard(3, 1)])
    assert cp.Odds(left).compare(other=right) == {'win': Fraction(1, 2), 'tie': Fraction(0), 'loss': Fraction(1, 2)}
    assert cp.Odds(left).compare(other=right, value=lambda c: 0, other_value=lambda c: 0) == {'win': Fraction(0), 'tie': Fraction(1), 'loss': Fraction(0)}


def test_odds_neither_mutate_state_nor_consume_randomness():
    """Fails if queries simulate draws or shuffle instead of exact counting."""
    rng = random.Random(384)
    deck = cp.Deck.standard(rng=rng)
    drawn = deck.draw(3)
    deck.discard(drawn[:1])
    before_cards, before_discards, before_rng = list(deck.cards), list(deck.discards), rng.getstate()
    odds = cp.Odds(deck)
    odds.count(4, lambda c: c.suit == 1)
    odds.reading(3, kind='highest')
    odds.compare()
    assert deck.cards == before_cards
    assert deck.discards == before_discards
    assert rng.getstate() == before_rng


def test_empty_sample_and_empty_deck_semantics():
    """Fails if zero draws divide by zero or empty extrema are accepted."""
    odds = cp.Odds(cp.Deck.from_cards([]))
    assert odds.count(0, lambda c: True) == {0: Fraction(1)}
    assert odds.counts(0, []) == {(): Fraction(1)}
    assert odds.reading(0) == {0: Fraction(1)}
    for kind in ('highest', 'lowest', 'kth'):
        with pytest.raises(ValueError):
            odds.reading(0, kind=kind, k=1)
    for replacement in (False, True):
        with pytest.raises(cp.DeckExhausted):
            odds.count(1, lambda c: True, replacement=replacement)


@pytest.mark.parametrize('n', [-1, 1.5, True, '2'])
def test_invalid_sample_sizes_rejected(n):
    """Fails if draw counts are silently coerced or booleans accepted as integers."""
    with pytest.raises((TypeError, ValueError)):
        cp.Odds(small_deck()).count(n, lambda c: True)


def test_invalid_readings_and_insufficient_dependent_cards():
    """Fails if invalid rank selectors or overlarge dependent samples are accepted."""
    odds = cp.Odds(small_deck())
    for k in (0, 4, True, 1.5):
        with pytest.raises((ValueError, TypeError)):
            odds.reading(3, kind='kth', k=k)
    with pytest.raises(ValueError):
        odds.reading(1, kind='median')
    with pytest.raises(cp.DeckExhausted):
        odds.reading(5)
    with pytest.raises(cp.DeckExhausted):
        odds.compare(3)


def test_exact_engine_reports_work_and_size_limits():
    """Fails if limit overflow approximates, hangs, or fails without naming a limit."""
    with pytest.raises(cp.OddsLimitError, match='(?i)(limit|work|budget)'):
        cp.Odds(small_deck(), max_work=1).reading(3)
    with pytest.raises(cp.OddsLimitError, match='100'):
        cp.Odds(small_deck()).reading(101, replacement=True)
    huge = cp.Deck.from_cards([cp.StandardCard(1, 0) for _ in range(10001)])
    with pytest.raises(cp.OddsLimitError, match='10.?000'):
        cp.Odds(huge).count(1, lambda c: True)


def test_seeded_dealing_agrees_with_exact_ace_fixture_within_six_standard_errors():
    """Fails if shuffling/dealing samples a different model from exact count odds."""
    trials = 6000
    probability = Fraction(18472, 54145)
    deck = cp.Deck.standard(jokers=False, seed=927341)
    hits = 0
    for _ in range(trials):
        deck.shuffle()
        cards = deck.draw(5)
        hits += any(c.rank_index == 0 for c in cards)
        deck.return_cards(cards)
    standard_error = math.sqrt(float(probability * (1 - probability)) / trials)
    assert abs(hits / trials - float(probability)) <= 6 * standard_error
