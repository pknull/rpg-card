"""The complete pre-0.3 names and deal order used by pk.asha remain stable."""

import pytest

import card_picker as cp


STANDARD_RANKS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
                  'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']
TAROT_RANKS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
               'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King']
TAROT_MAJORS = [
    'The Fool', 'The Magician', 'The High Priestess', 'The Empress',
    'The Emperor', 'The Hierophant', 'The Lovers', 'The Chariot',
    'Justice', 'The Hermit', 'Wheel of Fortune', 'Strength', 'The Hanged Man',
    'Death', 'Temperance', 'The Devil', 'The Tower', 'The Star', 'The Moon',
    'The Sun', 'Judgment', 'The World',
]
SHADOW_MAJORS = [
    'The Bastard', 'The Matrix', 'The High Priestess', 'Aes Sidhe Banrigh',
    'The Chief Executive', 'The Higher Power', 'The Avatars', 'The Ride',
    'Discipline', 'The Hermit', 'The Wheel of Fortune', 'The Vigilante',
    'The Hanged Man', '...404...', 'Threshold', 'The Dragon', 'The Tower',
    'The Comet', 'The Shadows', 'The Eclipse', 'Karma', 'The Awakened World',
]
UNO_RANKS = [
    'Zero', 'Skip', 'Draw Two', 'Reverse', 'One', 'Two', 'Three', 'Four',
    'Five', 'Six', 'Seven', 'Eight', 'Nine', 'One', 'Two', 'Three', 'Four',
    'Five', 'Six', 'Seven', 'Eight', 'Nine',
]


@pytest.mark.parametrize('cls,expected', [
    (cp.StandardCard, ['Joker', 'Joker'] + [f'{r} of {s}' for s in ['Hearts', 'Spades', 'Diamonds', 'Clubs'] for r in STANDARD_RANKS]),
    (cp.TarotCard, TAROT_MAJORS + [f'{r} of {s}' for s in ['Swords', 'Staves', 'Pentacles', 'Cups'] for r in TAROT_RANKS]),
    (cp.ShadowCard, SHADOW_MAJORS + [f'{r} of {s}' for s in ['Blades', 'Batons', 'Coins', 'Cups'] for r in TAROT_RANKS]),
    (cp.UnoCard, ['Wild'] * 4 + ['Wild Draw Four'] * 4 + [f'{s} {r}' for s in ['Red', 'Green', 'Blue', 'Yellow'] for r in UNO_RANKS]),
])
def test_complete_legacy_names_and_deal_order(cls, expected):
    """Fails if any legacy rank, suit, capitalization, composition, or deal order changes."""
    deck = cp.Deck(cls)
    deck.create()
    assert [c.name() for c in deck.cards] == expected
    assert deck.deal(len(expected) + 5) == expected[::-1]
    assert deck.deal() == []
    assert deck.deal(-1) == []


def test_legacy_bot_create_shuffle_deal_call_sequence():
    """Fails if existing constructor/create/shuffle/deal integrations stop working."""
    deck = cp.Deck(cp.StandardCard)
    assert deck.cards == []
    deck.create()
    deck.shuffle()
    names = deck.deal(5)
    assert len(names) == 5
    assert all(isinstance(name, str) for name in names)
    assert len(deck) == 49
