from card_picker import Deck, StandardCard


def test_standard_deck_size():
    deck = Deck(StandardCard)
    deck.create()
    assert len(deck) == 54


def test_deal_reduces_size():
    deck = Deck(StandardCard)
    deck.create()
    deck.shuffle()
    hand = deck.deal(5)
    assert len(hand) == 5
    assert len(deck) == 49
