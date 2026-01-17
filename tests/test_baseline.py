"""
Baseline tests documenting behavior of the card_picker module.

These tests verify correct behavior after bug fixes:
- TarotCard deck now has 78 cards (includes "Death")
- UnoCard.name() produces correct output ("Red Zero")
- Negative indices are validated and raise ValueError
"""

import pytest
from card_picker import Deck, StandardCard, TarotCard, ShadowCard, UnoCard


class TestDeckSizes:
    """Test deck sizes for all card types."""

    def test_standard_deck_size(self):
        """StandardCard deck should have 54 cards (2 jokers + 52 suited)."""
        deck = Deck(StandardCard)
        deck.create()
        assert len(deck) == 54

    def test_tarot_deck_size(self):
        """TarotCard deck has 78 cards (22 Major Arcana + 56 Minor Arcana)."""
        deck = Deck(TarotCard)
        deck.create()
        assert len(deck) == 78

    def test_shadow_deck_size(self):
        """ShadowCard deck should have 78 cards."""
        deck = Deck(ShadowCard)
        deck.create()
        assert len(deck) == 78

    def test_uno_deck_size(self):
        """UnoCard deck should have 96 cards (8 wild + 88 colored)."""
        deck = Deck(UnoCard)
        deck.create()
        assert len(deck) == 96


class TestStandardCardNaming:
    """Test StandardCard name formatting."""

    def test_ace_of_hearts(self):
        card = StandardCard(1, 0)
        assert card.name() == "Ace of Hearts"

    def test_king_of_spades(self):
        card = StandardCard(2, 12)
        assert card.name() == "King of Spades"

    def test_joker(self):
        card = StandardCard(0, 0)
        assert card.name() == "Joker"

    def test_second_joker(self):
        card = StandardCard(0, 1)
        assert card.name() == "Joker"

    def test_ten_of_diamonds(self):
        card = StandardCard(3, 9)
        assert card.name() == "Ten of Diamonds"

    def test_jack_of_clubs(self):
        card = StandardCard(4, 10)
        assert card.name() == "Jack of Clubs"


class TestTarotCardNaming:
    """Test TarotCard name formatting."""

    def test_ace_of_swords(self):
        card = TarotCard(1, 0)
        assert card.name() == "Ace of Swords"

    def test_king_of_cups(self):
        card = TarotCard(4, 13)
        assert card.name() == "King of Cups"

    def test_the_fool(self):
        card = TarotCard(0, 0)
        assert card.name() == "The Fool"

    def test_the_hanged_man(self):
        card = TarotCard(0, 12)
        assert card.name() == "The Hanged Man"

    def test_death_card(self):
        """Index 13 is Death (XIII)."""
        card = TarotCard(0, 13)
        assert card.name() == "Death"

    def test_temperance_card(self):
        """Index 14 is Temperance (XIV)."""
        card = TarotCard(0, 14)
        assert card.name() == "Temperance"

    def test_the_world(self):
        """The World is now at index 21 (XXI)."""
        card = TarotCard(0, 21)
        assert card.name() == "The World"

    def test_major_arcana_count(self):
        """TarotCard has 22 Major Arcana (0-XXI)."""
        assert len(TarotCard.MAJOR_NUMBERS) == 22


class TestShadowCardNaming:
    """Test ShadowCard name formatting."""

    def test_ace_of_blades(self):
        card = ShadowCard(1, 0)
        assert card.name() == "Ace of Blades"

    def test_the_bastard(self):
        card = ShadowCard(0, 0)
        assert card.name() == "The Bastard"

    def test_404_card(self):
        """The Shadow deck's version of Death."""
        card = ShadowCard(0, 13)
        assert card.name() == "...404..."

    def test_the_awakened_world(self):
        card = ShadowCard(0, 21)
        assert card.name() == "The Awakened World"

    def test_major_arcana_count(self):
        """ShadowCard correctly has 22 Major Arcana."""
        assert len(ShadowCard.MAJOR_NUMBERS) == 22


class TestUnoCardNaming:
    """Test UnoCard name formatting."""

    def test_wild_card(self):
        card = UnoCard(0, 0)
        assert card.name() == "Wild"

    def test_wild_draw_four(self):
        card = UnoCard(0, 4)
        assert card.name() == "Wild Draw Four"

    def test_red_zero(self):
        """UnoCard names are formatted as 'Color Number'."""
        card = UnoCard(1, 0)
        assert card.name() == "Red Zero"

    def test_blue_skip(self):
        card = UnoCard(3, 1)
        assert card.name() == "Blue Skip"

    def test_green_draw_two(self):
        card = UnoCard(2, 2)
        assert card.name() == "Green Draw Two"

    def test_yellow_nine(self):
        card = UnoCard(4, 12)
        assert card.name() == "Yellow Nine"


class TestDealBehavior:
    """Test Deck.deal() behavior including edge cases."""

    def test_deal_returns_card_names(self):
        deck = Deck(StandardCard)
        deck.create()
        hand = deck.deal(1)
        assert isinstance(hand, list)
        assert len(hand) == 1
        assert isinstance(hand[0], str)

    def test_deal_reduces_deck_size(self):
        deck = Deck(StandardCard)
        deck.create()
        initial_size = len(deck)
        deck.deal(5)
        assert len(deck) == initial_size - 5

    def test_deal_from_empty_deck(self):
        """Dealing from empty deck returns empty list."""
        deck = Deck(StandardCard)
        deck.create()
        deck.cards.clear()
        result = deck.deal(5)
        assert result == []
        assert len(deck) == 0

    def test_deal_more_than_available(self):
        """Dealing more cards than available returns what's left."""
        deck = Deck(StandardCard)
        deck.create()
        result = deck.deal(100)
        assert len(result) == 54
        assert len(deck) == 0

    def test_deal_zero_cards(self):
        """Dealing zero cards returns empty list."""
        deck = Deck(StandardCard)
        deck.create()
        result = deck.deal(0)
        assert result == []
        assert len(deck) == 54

    def test_deal_negative_cards(self):
        """Dealing negative cards returns empty list (range behavior)."""
        deck = Deck(StandardCard)
        deck.create()
        result = deck.deal(-5)
        assert result == []
        assert len(deck) == 54


class TestInputValidation:
    """Test input validation prevents invalid card creation."""

    def test_negative_suit_raises_error(self):
        """Negative suit raises ValueError."""
        with pytest.raises(ValueError, match="suit must be non-negative"):
            StandardCard(-1, 0)

    def test_negative_number_raises_error(self):
        """Negative number raises ValueError."""
        with pytest.raises(ValueError, match="number must be non-negative"):
            StandardCard(1, -1)

    def test_suit_out_of_range_raises_error(self):
        """Suit beyond valid range raises ValueError."""
        with pytest.raises(ValueError, match="suit .* out of range"):
            StandardCard(10, 0)

    def test_number_out_of_range_for_major_raises_error(self):
        """Number beyond major cards range raises ValueError."""
        with pytest.raises(ValueError, match="number .* out of range for major"):
            StandardCard(0, 100)

    def test_number_out_of_range_for_minor_raises_error(self):
        """Number beyond minor cards range raises ValueError."""
        with pytest.raises(ValueError, match="number .* out of range for minor"):
            StandardCard(1, 100)


class TestBackwardsCompatibility:
    """Test backwards compatibility helper methods."""

    def test_stringForSuit(self):
        card = StandardCard(1, 0)
        assert card.stringForSuit() == card.string_for_suit()
        assert card.stringForSuit() == " of Hearts"

    def test_stringForNumber(self):
        card = StandardCard(1, 0)
        assert card.stringForNumber() == card.string_for_number()
        assert card.stringForNumber() == "Ace"


class TestDeckOperations:
    """Test general Deck operations."""

    def test_deck_len(self):
        deck = Deck(StandardCard)
        assert len(deck) == 0
        deck.create()
        assert len(deck) == 54

    def test_create_clears_existing_cards(self):
        deck = Deck(StandardCard)
        deck.create()
        deck.deal(10)
        assert len(deck) == 44
        deck.create()
        assert len(deck) == 54

    def test_shuffle_maintains_size(self):
        deck = Deck(StandardCard)
        deck.create()
        deck.shuffle()
        assert len(deck) == 54
