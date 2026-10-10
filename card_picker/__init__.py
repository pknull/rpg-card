"""Simple playing card module for RPG helpers."""

from .Card import BaseCard, ShadowCard, StandardCard, TarotCard, UnoCard
from .Deck import Deck, DeckExhausted
from .Hand import Hand
from .Odds import Odds, OddsLimitError
from .State import SnapshotError, restore, snapshot

__version__ = "0.3.0"

__all__ = [
    "Deck",
    "DeckExhausted",
    "Hand",
    "Odds",
    "OddsLimitError",
    "SnapshotError",
    "snapshot",
    "restore",
    "BaseCard",
    "TarotCard",
    "ShadowCard",
    "StandardCard",
    "UnoCard",
]
