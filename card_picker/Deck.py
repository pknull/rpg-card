"""Container class for manipulating and dealing card objects."""

from random import shuffle


class Deck:
    """Represents a deck of cards built from a specific card system."""

    def __init__(self, card_system):
        self.card_system = card_system
        self.cards = []

    def __len__(self):
        return len(self.cards)

    def shuffle(self):
        """Shuffle the deck in place."""

        shuffle(self.cards)

    def deal(self, ncards=1):
        """Deal ``ncards`` cards, returning their names."""

        dealt = []
        for _ in range(ncards):
            if self.cards:
                dealt.append(self.cards.pop().name())
        return dealt

    def create(self):
        """Populate ``self.cards`` with a full set from ``card_system``."""

        self.cards.clear()

        for number in range(len(self.card_system.MAJOR_NUMBERS)):
            self.cards.append(self.card_system(0, number))

        for suit in range(1, len(self.card_system.SUITS)):
            for number in range(len(self.card_system.MINOR_NUMBERS)):
                self.cards.append(self.card_system(suit, number))
