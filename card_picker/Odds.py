"""Bounded exact distributions over the remaining physical cards in a deck.

This module uses grouped combinatorial counts, never random sampling. Callbacks
must be pure: queries themselves neither mutate decks nor consume randomness.
"""

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import islice
from math import comb
from numbers import Rational

from .Deck import DeckExhausted


class OddsLimitError(ValueError):
    """An exact query exceeded its documented size or work limit."""


class _Budget:
    def __init__(self, limit):
        self.limit = limit
        self.used = 0

    def spend(self):
        self.used += 1
        if self.used > self.limit:
            raise OddsLimitError(f"exact odds exceeded max_work={self.limit}")


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _numeric(value):
    if isinstance(value, bool) or not isinstance(value, Rational):
        raise ValueError("reading values must be exact rational numbers (int or Fraction)")
    return value


class _Reading:
    def __init__(self, kind, n, value=None, k=None):
        if kind not in ("sum", "highest", "lowest", "kth"):
            raise ValueError(f"unknown reading kind: {kind!r}")
        if kind != "sum" and n == 0:
            raise ValueError(f"{kind} requires at least one card")
        if kind == "kth":
            _integer(k, "k")
            if not 1 <= k <= n:
                raise ValueError("k must be between 1 and n (ascending, one-based)")
        elif k is not None:
            raise ValueError("k is only valid for a kth reading")
        if value is not None and not callable(value):
            raise TypeError("value must be callable")
        self.kind, self.k = kind, k
        self.value = value if value is not None else lambda card: card.value
        self.start = 0 if kind == "sum" else () if kind == "kth" else None

    def project(self, card):
        return _numeric(self.value(card))

    def add(self, state, value, count):
        if not count:
            return state
        if self.kind == "sum":
            return state + value * count
        if self.kind == "highest":
            return value if state is None else max(state, value)
        if self.kind == "lowest":
            return value if state is None else min(state, value)
        return tuple(sorted(state + (value,) * min(count, self.k))[:self.k])

    def finish(self, state):
        return state[-1] if self.kind == "kth" else state


class Odds:
    """Exact odds for the current draw pile, ignoring its known top order.

    Limits per query: 10,000 cards per deck, 100 total requested draws, and
    ``max_work`` DP transitions/comparison pairs (default 1,000,000). Exceeding
    any bound raises :class:`OddsLimitError`, never an approximation.
    """

    MAX_CARDS = 10_000
    MAX_DRAWS = 100

    def __init__(self, deck, *, max_work=1_000_000):
        _integer(max_work, "max_work")
        if not max_work:
            raise ValueError("max_work must be positive")
        self.deck, self.max_work = deck, max_work

    def _sample(self, deck, n, replacement):
        _integer(n, "n")
        if not isinstance(replacement, bool):
            raise ValueError("replacement must be a bool")
        if n > self.MAX_DRAWS:
            raise OddsLimitError(f"exact odds exceeded max_draws={self.MAX_DRAWS}")
        if len(deck.cards) > self.MAX_CARDS:
            raise OddsLimitError(f"exact odds exceeded max_cards={self.MAX_CARDS}")
        cards = tuple(deck.cards)
        if n and (not cards or (not replacement and n > len(cards))):
            raise DeckExhausted(f"cannot sample {n} cards from {len(cards)} remaining")
        return cards

    @staticmethod
    def _distribution(groups, n, replacement, start, update, budget):
        """Count subsets, or ordered replacement samples via multinomials."""
        if not n:
            return {start: Fraction(1)}
        size = sum(groups.values())
        remaining = size
        states = {(0, start): 1}
        for value, frequency in groups.items():
            remaining -= frequency
            following = defaultdict(int)
            for (drawn, state), weight in states.items():
                upper = n - drawn if replacement else min(frequency, n - drawn)
                lower = 0 if replacement else max(0, n - drawn - remaining)
                for count in range(lower, upper + 1):
                    budget.spend()
                    multiplicity = (comb(drawn + count, count) * frequency ** count
                                    if replacement else comb(frequency, count))
                    following[drawn + count, update(state, value, count)] += weight * multiplicity
            states = following
        denominator = size ** n if replacement else comb(size, n)
        return {state: Fraction(weight, denominator)
                for (drawn, state), weight in states.items() if drawn == n}

    def counts(self, n, predicates, *, replacement=False):
        """Joint matching counts, in predicate order; predicates may overlap.

        Disjoint exhaustive predicates give a multivariate hypergeometric
        distribution (multinomial with replacement). Keys are count tuples.
        """
        cards = self._sample(self.deck, n, replacement)
        predicates = tuple(islice(predicates, self.MAX_DRAWS + 1))
        # Bound signatures and tuple width as well as the state transitions.
        if len(predicates) > self.MAX_DRAWS:
            raise OddsLimitError(f"exact odds exceeded max_predicates={self.MAX_DRAWS}")
        if not all(callable(predicate) for predicate in predicates):
            raise TypeError("predicates must be callable")
        groups = Counter(tuple(int(bool(predicate(card))) for predicate in predicates)
                         for card in cards)
        start = (0,) * len(predicates)

        def update(state, signature, count):
            return tuple(old + match * count for old, match in zip(state, signature))

        return self._distribution(groups, n, replacement, start, update, _Budget(self.max_work))

    def count(self, n, predicate, *, replacement=False):
        """Distribution of the number of matching cards."""
        return {key[0]: probability for key, probability in
                self.counts(n, [predicate], replacement=replacement).items()}

    def reading(self, n, kind="sum", *, value=None, k=None, predicate=None,
                replacement=False):
        """Distribution of sum/highest/lowest/kth/count over ``n`` cards.

        ``kth`` is one-based ascending. ``count`` requires ``predicate``;
        other readings use ``value(card)`` (default ``card.value``).
        """
        cards = self._sample(self.deck, n, replacement)
        if kind == "count":
            if value is not None or k is not None:
                raise ValueError("count uses predicate, not value or k")
            return self.count(n, predicate, replacement=replacement)
        if predicate is not None:
            raise ValueError("predicate is only valid for a count reading")
        reading = _Reading(kind, n, value, k)
        return self._read(cards, n, replacement, reading, _Budget(self.max_work))

    def _read(self, cards, n, replacement, reading, budget):
        groups = Counter(reading.project(card) for card in cards)
        raw = self._distribution(groups, n, replacement, reading.start, reading.add, budget)
        result = defaultdict(Fraction)
        for state, probability in raw.items():
            result[reading.finish(state)] += probability
        return dict(result)

    def compare(self, n=1, *, other=None, other_n=None, kind="sum", other_kind=None,
                value=None, other_value=None, k=None, other_k=None, replacement=False):
        """Compare two readings: return win/tie/loss probabilities.

        With the same deck, samples are disjoint unless replacement is enabled.
        Separate decks are independent. Right-hand options inherit left-hand
        options when omitted; pass a distinct selector to override ``value``.
        For count comparisons use ``value=lambda card: int(condition(card))``.
        """
        other = self.deck if other is None else other
        other_n = n if other_n is None else other_n
        other_kind = kind if other_kind is None else other_kind
        other_value = value if other_value is None else other_value
        if other_k is None and other_kind == "kth":
            other_k = k
        left_cards = self._sample(self.deck, n, replacement)
        right_cards = self._sample(other, other_n, replacement)
        if n + other_n > self.MAX_DRAWS:
            raise OddsLimitError(f"exact odds exceeded max_draws={self.MAX_DRAWS}")
        shared = other is self.deck and not replacement
        if shared and n + other_n > len(left_cards):
            raise DeckExhausted(f"cannot sample {n + other_n} disjoint cards from {len(left_cards)} remaining")
        left = _Reading(kind, n, value, k)
        right = _Reading(other_kind, other_n, other_value, other_k)
        budget = _Budget(self.max_work)
        result = dict.fromkeys(("win", "tie", "loss"), Fraction())
        if shared:
            groups = Counter((left.project(card), right.project(card)) for card in left_cards)
            states = {(0, 0, left.start, right.start): 1}
            remaining = len(left_cards)
            for (lv, rv), frequency in groups.items():
                remaining -= frequency
                following = defaultdict(int)
                for (i, j, ls, rs), weight in states.items():
                    for a in range(max(0, n - i - remaining), min(frequency, n - i) + 1):
                        for b in range(max(0, other_n - j - remaining),
                                       min(frequency - a, other_n - j) + 1):
                            budget.spend()
                            if n + other_n - i - j - a - b > remaining:
                                continue
                            key = (i + a, j + b, left.add(ls, lv, a), right.add(rs, rv, b))
                            following[key] += weight * comb(frequency, a) * comb(frequency - a, b)
                states = following
            denominator = comb(len(left_cards), n) * comb(len(left_cards) - n, other_n)
            for (i, j, ls, rs), weight in states.items():
                if i == n and j == other_n:
                    outcome = self._outcome(left.finish(ls), right.finish(rs))
                    result[outcome] += Fraction(weight, denominator)
        else:
            ld = self._read(left_cards, n, replacement, left, budget)
            rd = self._read(right_cards, other_n, replacement, right, budget)
            for lv, lp in ld.items():
                for rv, rp in rd.items():
                    budget.spend()
                    result[self._outcome(lv, rv)] += lp * rp
        return result

    @staticmethod
    def _outcome(left, right):
        return "win" if left > right else "loss" if left < right else "tie"
