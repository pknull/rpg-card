"""Physical card ownership, draw piles, discards and reproducible shuffling."""

from collections.abc import Mapping
import math
from numbers import Real
import random

from .Card import BaseCard, ShadowCard, StandardCard, TarotCard, UnoCard, validate_value_map


class DeckExhausted(ValueError):
    """A requested draw cannot be satisfied by the remaining draw pile."""


def _count(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("card count must be an integer")
    if n < 0:
        raise ValueError("card count must be non-negative")


class Deck:
    """A list-tail draw pile with exclusive ownership of physical cards.

    ``cards`` remains public for legacy callers. Use transfer methods rather
    than editing the list when ownership, hands or recall must stay coherent.
    """

    def __init__(self, card_system, *, seed=None, rng=None, value_map=None):
        if seed is not None and rng is not None:
            raise ValueError("specify seed or rng, not both")
        if rng is not None and not isinstance(rng, random.Random):
            raise TypeError("rng must be a random.Random instance")
        self.card_system = card_system
        self.cards = []
        self.discards = []
        self._owned = set()
        self._out = {}
        self._rng = rng if rng is not None else random.Random(seed) if seed is not None else random
        self._value_map = validate_value_map(value_map)
        self._build_options = {}

    def __len__(self):
        return len(self.cards)

    @classmethod
    def standard(cls, *, jokers=True, **kwargs):
        if not isinstance(jokers, bool):
            raise TypeError("jokers must be a boolean")
        deck = cls(StandardCard, **kwargs)
        if not jokers:
            deck._build_options = {"jokers": False}
        deck.create()
        return deck

    @classmethod
    def tarot(cls, *, arcana=None, **kwargs):
        if arcana not in (None, "major", "minor"):
            raise ValueError("arcana must be 'major', 'minor', or None")
        deck = cls(TarotCard, **kwargs)
        if arcana is not None:
            deck._build_options = {"arcana": arcana}
        deck.create()
        return deck

    @classmethod
    def shadow(cls, **kwargs):
        deck = cls(ShadowCard, **kwargs)
        deck.create()
        return deck

    @classmethod
    def uno(cls, **kwargs):
        deck = cls(UnoCard, **kwargs)
        deck.create()
        return deck

    @staticmethod
    def _batch(cards):
        cards = list(cards)
        if any(not isinstance(card, BaseCard) for card in cards):
            raise TypeError("expected card objects")
        if len({id(card) for card in cards}) != len(cards):
            raise ValueError("duplicate physical card in transfer")
        if len({card.card_id for card in cards}) != len(cards):
            raise ValueError("duplicate persistent card ID in transfer")
        return cards

    @classmethod
    def from_cards(cls, cards, *, seed=None, rng=None):
        """Adopt unowned cards, preserving their list order and attributes."""
        cards = cls._batch(cards)
        if any(card._owner is not None for card in cards):
            raise ValueError("card already belongs to a deck")
        deck = cls(None, seed=seed, rng=rng)
        deck._adopt(cards)
        deck.cards.extend(cards)
        return deck

    def _adopt(self, cards):
        for card in cards:
            card._owner = self
            self._owned.add(card)

    @staticmethod
    def _release_hand(card):
        if card._hand is not None:
            card._hand.cards.remove(card)
            card._hand = None

    def _detach(self, cards):
        for card in cards:
            self._release_hand(card)
            self._owned.discard(card)
            self._out.pop(card, None)
            card._owner = None

    def create(self):
        """Replace all zones with a full set; release old cards and hands."""
        if self.card_system is None:
            raise ValueError("a composed deck has no card system to create")
        cards = []
        # Major-only custom systems may inherit BaseCard's empty SUITS list.
        for suit in range(max(1, len(self.card_system.SUITS))):
            numbers = self.card_system.MINOR_NUMBERS if suit else self.card_system.MAJOR_NUMBERS
            for number in range(len(numbers)):
                if self._value_map:
                    card = self.card_system(suit, number, value_map=self._value_map)
                else:
                    card = self.card_system(suit, number)
                cards.append(card)
        if self._build_options.get("jokers") is False:
            cards = [card for card in cards if card.suit != 0]
        if "arcana" in self._build_options:
            cards = [card for card in cards if card.arcana == self._build_options["arcana"]]
        self._detach(list(self._owned))
        self.cards.clear()
        self.discards.clear()
        self._adopt(cards)
        self.cards.extend(cards)

    @staticmethod
    def _orientation_args(size, upright_probability, upright_count):
        if isinstance(upright_probability, bool) or not isinstance(upright_probability, Real):
            raise TypeError("upright_probability must be a real probability")
        if not math.isfinite(upright_probability) or not 0 <= upright_probability <= 1:
            raise ValueError("upright_probability must be between zero and one")
        if upright_count is not None:
            _count(upright_count)
            if upright_count > size:
                raise ValueError("upright_count exceeds draw pile size")

    def shuffle(self, *, upright_probability=0.5, upright_count=None):
        """Shuffle the draw pile, then assign independent or fixed orientation."""
        self._orientation_args(len(self.cards), upright_probability, upright_count)
        self._rng.shuffle(self.cards)
        if upright_count is None:
            for card in self.cards:
                card.orientation = "upright" if self._rng.random() < upright_probability else "reversed"
        else:
            upright = set(self._rng.sample(range(len(self.cards)), upright_count))
            for i, card in enumerate(self.cards):
                card.orientation = "upright" if i in upright else "reversed"

    def _take(self):
        card = self.cards.pop()
        self._out[card] = None
        return card

    def deal(self, ncards=1):
        """Return legacy names, allowing short, empty and negative deals."""
        dealt = []
        for _ in range(ncards):
            if self.cards:
                dealt.append(self._take().name())
        return dealt

    def draw(self, n=1):
        """Return n physical cards, or raise without changing the deck."""
        _count(n)
        if n > len(self.cards):
            raise DeckExhausted(f"requested {n} cards; only {len(self.cards)} remain")
        return [self._take() for _ in range(n)]

    def peek(self, n=1):
        """Return up to n cards in draw order without consuming them."""
        _count(n)
        return list(reversed(self.cards[-n:])) if n else []

    def draw_until(self, predicate):
        """Draw through the first match; exhaustion consumes the remaining pile."""
        if not callable(predicate):
            raise TypeError("predicate must be callable")
        cards = []
        while self.cards:
            card = self._take()
            cards.append(card)
            if predicate(card):
                return cards
        raise DeckExhausted("draw pile exhausted without a matching card")

    def discard(self, cards):
        """Move this deck's drawn or held cards into its discard pile."""
        cards = self._batch(cards)
        if any(card._owner is not self or card not in self._out for card in cards):
            raise ValueError("only drawn or held cards can be discarded")
        for card in cards:
            self._release_hand(card)
            del self._out[card]
        self.discards.extend(cards)

    def return_cards(self, cards, *, top=True):
        """Return out/discarded cards or adopt unowned cards, first card first."""
        if not isinstance(top, bool):
            raise TypeError("top must be a boolean")
        cards = self._batch(cards)
        available = self._out.keys() | set(self.discards)
        if any(card._owner is not None and (
            card._owner is not self or card not in available
        ) for card in cards):
            raise ValueError("card is already in a draw pile or belongs to another deck")
        owned_ids = {card.card_id: card for card in self._owned}
        if any(card.card_id in owned_ids and owned_ids[card.card_id] is not card
               for card in cards):
            raise ValueError("duplicate persistent card ID in deck")
        for card in cards:
            self._release_hand(card)
            self._out.pop(card, None)
        returning = set(cards)
        self.discards[:] = [card for card in self.discards if card not in returning]
        self._adopt(cards)
        if top:
            self.cards.extend(reversed(cards))
        else:
            self.cards[0:0] = reversed(cards)

    def reshuffle(self, *, all_cards=False, upright_probability=0.5, upright_count=None):
        """Mix in discards; optionally recall all dealt, drawn and held cards."""
        if not isinstance(all_cards, bool):
            raise TypeError("all_cards must be a boolean")
        # Dict insertion order makes recalled draws reproducible across runs.
        recalled = list(self.discards)
        if all_cards:
            recalled.extend(self._out)
        self._orientation_args(len(self.cards) + len(recalled), upright_probability, upright_count)
        for card in recalled:
            self._release_hand(card)
            self._out.pop(card, None)
        self.cards.extend(recalled)
        self.discards.clear()
        self.shuffle(upright_probability=upright_probability, upright_count=upright_count)

    def remove(self, *, suit=None, rank=None, arcana=None, predicate=None):
        """Detach remaining cards matching every supplied selector."""
        for selector in (suit, rank):
            if selector is not None:
                _count(selector)
        if arcana not in (None, "major", "minor"):
            raise ValueError("arcana must be 'major', 'minor', or None")
        if predicate is not None and not callable(predicate):
            raise TypeError("predicate must be callable")
        removed = [card for card in self.cards if
                   (suit is None or card.suit == suit) and
                   (rank is None or card.rank_index == rank) and
                   (arcana is None or card.arcana == arcana) and
                   (predicate is None or predicate(card))]
        selected = set(removed)
        self.cards[:] = [card for card in self.cards if card not in selected]
        self._detach(removed)
        return removed

    @classmethod
    def combine(cls, *decks, seed=None, rng=None):
        """Move remaining cards into one deck; source out/discard zones stay."""
        if any(not isinstance(deck, Deck) for deck in decks):
            raise TypeError("combine requires Deck objects")
        if len({id(deck) for deck in decks}) != len(decks):
            raise ValueError("cannot combine the same deck twice")
        cls._batch(card for deck in decks for card in deck.cards)
        combined = cls(None, seed=seed, rng=rng)
        for deck in decks:
            cards = list(deck.cards)
            deck._detach(cards)
            deck.cards.clear()
            combined._adopt(cards)
            combined.cards.extend(cards)
        return combined

    def split(self, piles):
        """Partition remaining cards exactly once into named decks, atomically."""
        if not isinstance(piles, Mapping):
            raise TypeError("piles must map names to predicates")
        if any(not isinstance(name, str) or not callable(predicate) for name, predicate in piles.items()):
            raise TypeError("pile names must be strings and predicates callable")
        partition = {name: [] for name in piles}
        for card in self.cards:
            matches = [name for name, predicate in piles.items() if predicate(card)]
            if len(matches) != 1:
                raise ValueError("each remaining card must match exactly one pile")
            partition[matches[0]].append(card)
        # Children share this deck's RNG stream; module random remains the default.
        result = {name: type(self)(None) for name in piles}
        self._detach(list(self.cards))
        self.cards.clear()
        for name, cards in partition.items():
            result[name]._rng = self._rng
            result[name]._adopt(cards)
            result[name].cards.extend(cards)
        return result
