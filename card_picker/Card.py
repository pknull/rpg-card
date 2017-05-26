class TarotCard:
    SUITS = ['', 'Swords', 'Staves', 'Pentacles', 'Cups']

    MINOR_NUMBERS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six',
                     'Seven', 'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King']

    MAJOR_NUMBERS = ['The Fool', 'The Magician', 'The High Priestess',
                     'The Empress', 'The Emperor', 'The Heirophant', 'The Lovers',
                     'The Chariot', 'Justice', 'The Hermit', 'Wheel of Fortune',
                     'Strength', 'The Hanged Man', 'Temperance', 'The Devil',
                     'The Tower', 'The Star', 'The Moon', 'The Sun', 'Judgment', 'The World']

    def __init__(self, newSuit, newNumber):

        self.suit = newSuit
        self.number = newNumber

    def stringForSuit(self):

        if self.suit > 0:
            return ' of ' + TarotCard.SUITS[self.suit]
        else:
            return ''

    def stringForNumber(self):

        if self.suit > 0:
            return TarotCard.MINOR_NUMBERS[self.number]
        else:
            return TarotCard.MAJOR_NUMBERS[self.number]

    def name(self):

        return self.stringForNumber() + self.stringForSuit()


class ShadowCard:
    SUITS = ['', 'Blades', 'Batons', 'Coins', 'Cups']

    MINOR_NUMBERS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six',
                     'Seven', 'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King']

    MAJOR_NUMBERS = ['The Bastard', 'The Matrix', 'The High Priestess',
                     'Aes Sidhe Banrigh', 'The Chief Executive', 'The Higher Power',
                     'The Avatars', 'The Ride', 'Discipline', 'The Hermit',
                     'The Wheel of Fortune', 'The Vigilante', 'The Hanged Man', '...404...',
                     'Threshold', 'The Dragon', 'The Tower', 'The Comet', 'The Shadows',
                     'The Eclipse', 'Karma', 'The Awakened World']

    def __init__(self, newSuit, newNumber):

        self.suit = newSuit
        self.number = newNumber

    def stringForSuit(self):

        if self.suit > 0:
            return ' of ' + ShadowCard.SUITS[self.suit]
        else:
            return ''

    def stringForNumber(self):

        if self.suit > 0:
            return ShadowCard.MINOR_NUMBERS[self.number]
        else:
            return ShadowCard.MAJOR_NUMBERS[self.number]

    def name(self):

        return self.stringForNumber() + self.stringForSuit()


class StandardCard:
    SUITS = ['', 'Hearts', 'Spades', 'Diamonds', 'Clubs']

    MINOR_NUMBERS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']

    MAJOR_NUMBERS = ['Joker','Joker']

    def __init__(self, newSuit, newNumber):
        self.suit = newSuit
        self.number = newNumber

    def stringForSuit(self):

        if self.suit > 0:
            return ' of ' + self.SUITS[self.suit]
        else:
            return ''

    def stringForNumber(self):

        if self.suit > 0:
            return self.MINOR_NUMBERS[self.number]
        else:
            return self.MAJOR_NUMBERS[self.number]

    def name(self):

        return self.stringForNumber() + self.stringForSuit()

