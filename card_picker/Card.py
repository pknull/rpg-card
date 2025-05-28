class BaseCard:
    """Base class used to define card systems."""

    SUITS = []
    MINOR_NUMBERS = []
    MAJOR_NUMBERS = []

    def __init__(self, suit, number):
        self.suit = suit
        self.number = number

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
        return f"{self.SUITS[self.suit]} " if self.suit > 0 else ""
