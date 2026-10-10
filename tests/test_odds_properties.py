"""Independent exhaustive probes beyond the requirements' named fixtures."""

from collections import Counter
from fractions import Fraction
from itertools import permutations, product

import pytest

from card_picker import Deck, StandardCard
import card_picker as cp


def deck_with_values(values):
    return Deck.from_cards([
        StandardCard(1, i, value_map={i: value}) for i, value in enumerate(values)
    ])


def summarize(kind, values):
    if kind == "sum":
        return sum(values)
    if kind == "highest":
        return max(values)
    if kind == "lowest":
        return min(values)
    return sorted(values)[0]


@pytest.mark.parametrize("replacement", [False, True])
@pytest.mark.parametrize("sizes", [(1, 1), (1, 2), (2, 2)])
@pytest.mark.parametrize("kinds", [
    ("sum", "sum"), ("highest", "lowest"), ("lowest", "highest"),
    ("kth", "sum"), ("sum", "kth"),
])
def test_joint_readings_with_distinct_projections(replacement, sizes, kinds):
    # Different selectors must not destroy correlation within a physical card.
    values = [Fraction(-1, 2), 0, Fraction(3, 2), 0]
    n, m = sizes
    kind, other_kind = kinds
    samples = (product(range(4), repeat=n + m) if replacement
               else permutations(range(4), n + m))
    tally = Counter()
    for sample in samples:
        left = summarize(kind, [values[i] for i in sample[:n]])
        right = summarize(other_kind, [2 - values[i] for i in sample[n:]])
        tally["win" if left > right else "loss" if left < right else "tie"] += 1
    expected = {key: Fraction(tally[key], sum(tally.values()))
                for key in ("win", "tie", "loss")}
    options = {}
    if kind == "kth":
        options["k"] = 1
    if other_kind == "kth":
        options["other_k"] = 1
    actual = cp.Odds(deck_with_values(values)).compare(
        n, other_n=m, kind=kind, other_kind=other_kind,
        other_value=lambda card: 2 - card.value, replacement=replacement, **options,
    )
    assert actual == expected


@pytest.mark.parametrize("replacement", [False, True])
def test_zero_samples_and_zero_sided_comparison(replacement):
    odds = cp.Odds(deck_with_values([1, 2, 2]))
    assert odds.counts(0, [lambda c: True], replacement=replacement) == {(0,): Fraction(1)}
    assert odds.counts(3, [], replacement=replacement) == {(): Fraction(1)}
    assert odds.compare(0, replacement=replacement) == {
        "win": Fraction(0), "tie": Fraction(1), "loss": Fraction(0),
    }
    assert odds.compare(0, other_n=1, replacement=replacement) == {
        "win": Fraction(0), "tie": Fraction(0), "loss": Fraction(1),
    }


def test_live_query_after_return_discard_and_attribute_change():
    deck = deck_with_values([1, 2, 3])
    odds = cp.Odds(deck)
    card = deck.draw()[0]
    deck.discard([card])
    assert odds.reading(2) == {3: Fraction(1)}
    deck.return_cards([card])
    card.value = 5
    assert odds.reading(3) == {8: Fraction(1)}


@pytest.mark.parametrize("bad", [True, 0.5, float("nan"), "1", None])
def test_nonexact_projections_rejected(bad):
    with pytest.raises(ValueError, match="rational"):
        cp.Odds(deck_with_values([1])).reading(1, value=lambda c: bad)


def test_zero_work_and_predicate_width_limits():
    deck = deck_with_values([1])
    for bad in (0, -1, True, 0.5):
        with pytest.raises(ValueError):
            cp.Odds(deck, max_work=bad)
    with pytest.raises(cp.OddsLimitError, match="max_predicates=100"):
        cp.Odds(deck).counts(1, [lambda c: True] * 101)


def test_predicate_generator_is_bounded_before_exhaustion():
    def too_many():
        for _ in range(102):
            yield lambda c: True
        raise AssertionError("predicate limit must stop reading the generator")

    with pytest.raises(cp.OddsLimitError, match="max_predicates=100"):
        cp.Odds(deck_with_values([1])).counts(1, too_many())


def test_limit_failures_leave_live_state_and_rng_unchanged():
    deck = Deck.standard(seed=55)
    deck.shuffle()
    before = list(deck.cards)
    orientations = [c.orientation for c in before]
    with pytest.raises(cp.OddsLimitError, match="max_work=1"):
        cp.Odds(deck, max_work=1).compare(2)
    assert deck.cards == before
    assert [c.orientation for c in deck.cards] == orientations
