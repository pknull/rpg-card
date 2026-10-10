from collections.abc import Mapping
from fractions import Fraction
from numbers import Rational
from uuid import uuid4


def validate_value_map(value_map):
    """Copy and validate exact rank or (suit, rank) overrides."""
    if value_map is None:
        return {}
    if not isinstance(value_map, Mapping):
        raise TypeError("value_map must be a mapping")
    result = {}
    for key, value in value_map.items():
        parts = key if isinstance(key, tuple) else (key,)
        if (isinstance(key, tuple) and len(key) != 2) or any(
            isinstance(part, bool) or not isinstance(part, int) or part < 0
            for part in parts
        ):
            raise ValueError("value_map keys must be ranks or (suit, rank) pairs")
        if isinstance(value, bool) or not isinstance(value, Rational):
            raise TypeError("card values must be exact rational numbers")
        result[key] = value if isinstance(value, int) else Fraction(value)
    return result


class BaseCard:
    """Base class used to define card systems."""

    SUITS = []
    MINOR_NUMBERS = []
    MAJOR_NUMBERS = []

    def __init__(self, suit, number, *, value_map=None):
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (suit, number)):
            raise TypeError("suit and number must be integers")
        if suit < 0:
            raise ValueError(f"suit must be non-negative, got {suit}")
        if number < 0:
            raise ValueError(f"number must be non-negative, got {number}")
        if suit == 0:
            if number >= len(self.MAJOR_NUMBERS):
                raise ValueError(
                    f"number {number} out of range for major cards "
                    f"(max {len(self.MAJOR_NUMBERS) - 1})"
                )
        else:
            if suit >= len(self.SUITS):
                raise ValueError(
                    f"suit {suit} out of range (max {len(self.SUITS) - 1})"
                )
            if number >= len(self.MINOR_NUMBERS):
                raise ValueError(
                    f"number {number} out of range for minor cards "
                    f"(max {len(self.MINOR_NUMBERS) - 1})"
                )
        self.suit = suit
        self.number = number
        mapping = validate_value_map(value_map)
        self.value = mapping.get((suit, number), mapping.get(number, self._default_value()))
        self.orientation = "upright"
        self._owner = None
        self._hand = None
        self._card_id = uuid4().hex

    @property
    def card_id(self):
        """Stable physical-card identity for storage and later commands."""
        return self._card_id

    @property
    def rank_index(self):
        return self.number

    @property
    def colour(self):
        return None

    @property
    def arcana(self):
        return None

    def _default_value(self):
        return self.number + 1 if self.suit else 0

    def string_for_suit(self):
        return f" of {self.SUITS[self.suit]}" if self.suit > 0 else ""

    def string_for_number(self):
        return (
            self.MINOR_NUMBERS[self.number]
            if self.suit > 0
            else self.MAJOR_NUMBERS[self.number]
        )

    def name(self):
        return self.string_for_number() + self.string_for_suit()

    # Backwards compatibility helpers
    def stringForSuit(self):
        return self.string_for_suit()

    def stringForNumber(self):
        return self.string_for_number()


class TarotCard(BaseCard):
    @property
    def arcana(self):
        return "minor" if self.suit else "major"

    def _default_value(self):
        return self.number + 1 if self.suit else self.number

    SUITS = ["", "Swords", "Staves", "Pentacles", "Cups"]

    MINOR_NUMBERS = [
        "Ace",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Page",
        "Knight",
        "Queen",
        "King",
    ]

    MAJOR_NUMBERS = [
        "The Fool",
        "The Magician",
        "The High Priestess",
        "The Empress",
        "The Emperor",
        "The Hierophant",
        "The Lovers",
        "The Chariot",
        "Justice",
        "The Hermit",
        "Wheel of Fortune",
        "Strength",
        "The Hanged Man",
        "Death",
        "Temperance",
        "The Devil",
        "The Tower",
        "The Star",
        "The Moon",
        "The Sun",
        "Judgment",
        "The World",
    ]


class ShadowCard(BaseCard):
    @property
    def arcana(self):
        return "minor" if self.suit else "major"

    def _default_value(self):
        return self.number + 1 if self.suit else self.number

    SUITS = ["", "Blades", "Batons", "Coins", "Cups"]

    MINOR_NUMBERS = [
        "Ace",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Page",
        "Knight",
        "Queen",
        "King",
    ]

    MAJOR_NUMBERS = [
        "The Bastard",
        "The Matrix",
        "The High Priestess",
        "Aes Sidhe Banrigh",
        "The Chief Executive",
        "The Higher Power",
        "The Avatars",
        "The Ride",
        "Discipline",
        "The Hermit",
        "The Wheel of Fortune",
        "The Vigilante",
        "The Hanged Man",
        "...404...",
        "Threshold",
        "The Dragon",
        "The Tower",
        "The Comet",
        "The Shadows",
        "The Eclipse",
        "Karma",
        "The Awakened World",
    ]


class StandardCard(BaseCard):
    @property
    def colour(self):
        if not self.suit:
            return None
        return "red" if self.suit in (1, 3) else "black"

    SUITS = ["", "Hearts", "Spades", "Diamonds", "Clubs"]

    MINOR_NUMBERS = [
        "Ace",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Jack",
        "Queen",
        "King",
    ]

    MAJOR_NUMBERS = ["Joker", "Joker"]


class UnoCard(BaseCard):

    def _default_value(self):
        return (self.number - 4) % 9 + 1 if self.suit and self.number >= 4 else 0

    SUITS = ["", "Red", "Green", "Blue", "Yellow"]

    MINOR_NUMBERS = [
        "Zero",
        "Skip",
        "Draw Two",
        "Reverse",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
    ]

    MAJOR_NUMBERS = [
        "Wild",
        "Wild",
        "Wild",
        "Wild",
        "Wild Draw Four",
        "Wild Draw Four",
        "Wild Draw Four",
        "Wild Draw Four",
    ]

    def string_for_suit(self):
        return self.SUITS[self.suit] if self.suit > 0 else ""

    def name(self):
        if self.suit > 0:
            return f"{self.string_for_suit()} {self.string_for_number()}"
        return self.string_for_number()
