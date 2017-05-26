from random import shuffle

from card_picker.Card import *

class Deck:
    def __init__(self, card_name):

        self.cards = []
        self.card_name = card_name

    def shuffle(self):

        shuffle(self.cards)

    def deal(self, ncards=1):
        result = []
        for x in range(0, ncards):
            if len(self.cards):
                result.append(self.cards.pop().name())
        return result

    def reset(self):

        card_conv = {
            'standard' : StandardCard,
            'shadow' : ShadowCard,
            'tarot' : TarotCard
        }

        card_system = card_conv[self.card_name]

        for card in self.cards:
            self.cards.pop()

        for number in range(0, len(card_system.MAJOR_NUMBERS)):
            self.cards.append(card_system(0, number))

        for suit in range(1, len(card_system.SUITS)):
            for number in range(0, len(card_system.MINOR_NUMBERS)):
                self.cards.append(card_system(suit, number))

