"""A hand references drawn cards owned by one deck."""

from .Deck import Deck


class Hand:
    """Draw into a hand; playing leaves the card out, discarding returns it."""

    def __init__(self, deck):
        if not isinstance(deck, Deck):
            raise TypeError("a hand requires a Deck")
        self.deck = deck
        self.cards = []

    def __len__(self):
        return len(self.cards)

    def draw(self, n=1):
        cards = self.deck.draw(n)
        for card in cards:
            card._hand = self
        self.cards.extend(cards)
        return cards

    def play(self, card):
        """Release one card from the hand while leaving it out of the deck."""
        self._validate([card])
        self.deck._release_hand(card)
        return card

    def _validate(self, cards):
        cards = self.deck._batch(cards)
        if any(card._hand is not self or card not in self.cards or
               card._owner is not self.deck or card not in self.deck._out
               for card in cards):
            raise ValueError("card is not held in this hand")
        return cards

    def discard(self, cards):
        """Discard a validated batch from this hand to its deck."""
        self.deck.discard(self._validate(cards))
