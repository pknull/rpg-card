from random import shuffle

class Deck:
    def __init__(self, card_system):

        self.cards = []
        self.card_system = card_system

    def shuffle(self):

        shuffle(self.cards)

    def deal(self, ncards=1):
        result = []
        for x in range(0, ncards):
            if len(self.cards):
                result.append(self.cards.pop().name())
        return result

    # this is a bit hacky at the moment, will clean up later
    def create(self):

        for card in self.cards:
            self.cards.pop()

        for number in range(0, len(self.card_system.MAJOR_NUMBERS)):
            self.cards.append(self.card_system(0, number))

        for suit in range(1, len(self.card_system.SUITS)):
            for number in range(0, len(self.card_system.MINOR_NUMBERS)):
                self.cards.append(self.card_system(suit, number))

