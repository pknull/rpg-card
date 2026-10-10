"""Versioned JSON-compatible snapshots; no storage, pickle or class imports.

The caller must serialize access while taking/replacing a snapshot. Restoration
creates a separate object graph and never rewinds the process-global RNG.
"""

from collections.abc import Mapping
from fractions import Fraction
import math
from numbers import Rational
import random

from .Card import ShadowCard, StandardCard, TarotCard, UnoCard
from .Deck import Deck
from .Hand import Hand


class SnapshotError(ValueError):
    """Unsupported snapshot data or an inconsistent live deck/hand graph."""


_SYSTEMS = {"standard": StandardCard, "tarot": TarotCard,
            "shadow": ShadowCard, "uno": UnoCard}
_NAMES = {cls: name for name, cls in _SYSTEMS.items()}
_MAX_CARDS = 10_000
_MAX_HANDS = 1_000
_MAX_BITS = 4_096
_ROOT_KEYS = {"format", "version", "deck", "cards", "draw_pile", "discards",
              "drawn", "hands", "rng"}


def _object(value, keys, where):
    if type(value) is not dict or value.keys() != keys:
        raise SnapshotError(f"{where} must be an object with exactly {sorted(keys)}")


def _list(value, limit, where):
    if type(value) is not list:
        raise SnapshotError(f"{where} must be a list")
    if len(value) > limit:
        raise SnapshotError(f"{where} exceeds limit {limit}")


def _integer(value, where, *, minimum=None, maximum=None):
    if type(value) is not int or value.bit_length() > _MAX_BITS:
        raise SnapshotError(f"{where} must be an integer of at most {_MAX_BITS} bits")
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise SnapshotError(f"{where} is outside the allowed range")


def _id(value):
    if (type(value) is not str or len(value) != 32 or
            any(char not in "0123456789abcdef" for char in value)):
        raise SnapshotError("card ID must be 32 lowercase hexadecimal characters")


def _name(value):
    if type(value) is not str or not 1 <= len(value) <= 256:
        raise SnapshotError("hand name must be a string of 1 to 256 characters")


def _value(value):
    _list(value, 2, "rational value")
    if len(value) != 2:
        raise SnapshotError("rational value must be [numerator, denominator]")
    _integer(value[0], "numerator")
    _integer(value[1], "denominator", minimum=1)
    return Fraction(*value)


def _encode_value(value):
    if isinstance(value, bool) or not isinstance(value, Rational):
        raise SnapshotError("card values must be exact rational numbers")
    pair = [int(value.numerator), int(value.denominator)]
    _value(pair)
    return pair


def _recipe(recipe):
    _object(recipe, {"system", "options", "value_map"}, "deck")
    system = recipe["system"]
    if system is not None and (type(system) is not str or system not in _SYSTEMS):
        raise SnapshotError("unsupported deck system")
    options = recipe["options"]
    if type(options) is not dict:
        raise SnapshotError("deck options must be an object")
    if options:
        if system == "standard":
            _object(options, {"jokers"}, "standard options")
            if type(options["jokers"]) is not bool:
                raise SnapshotError("jokers must be a boolean")
        elif system == "tarot":
            _object(options, {"arcana"}, "tarot options")
            if options["arcana"] not in ("major", "minor"):
                raise SnapshotError("arcana must be major or minor")
        else:
            raise SnapshotError("this deck system has no builder options")
    entries = recipe["value_map"]
    _list(entries, _MAX_CARDS, "value_map")
    if system is None and entries:
        raise SnapshotError("a composed deck has no rebuild value_map")
    mapping = {}
    for entry in entries:
        _object(entry, {"suit", "rank", "value"}, "value_map entry")
        cls = _SYSTEMS[system]
        suit = entry["suit"]
        if suit is not None:
            _integer(suit, "mapped suit", minimum=0, maximum=len(cls.SUITS) - 1)
            rank_count = len(cls.MINOR_NUMBERS if suit else cls.MAJOR_NUMBERS)
        else:
            rank_count = max(len(cls.MINOR_NUMBERS), len(cls.MAJOR_NUMBERS))
        # Validate against the full system, not the possibly depleted selection.
        # Bounded indices also prevent collision-heavy arbitrary integer keys.
        _integer(entry["rank"], "mapped rank", minimum=0, maximum=rank_count - 1)
        key = entry["rank"] if suit is None else (suit, entry["rank"])
        if key in mapping:
            raise SnapshotError("duplicate value_map key")
        mapping[key] = _value(entry["value"])
    return _SYSTEMS.get(system), dict(options), mapping


def _rng_state(data):
    _object(data, {"algorithm", "state"}, "rng")
    if data["algorithm"] != "python.random.MT19937":
        raise SnapshotError("unsupported RNG algorithm")
    state = data["state"]
    _list(state, 3, "RNG state")
    if len(state) != 3 or type(state[0]) is not int or state[0] != 3:
        raise SnapshotError("RNG state must use Python state version 3")
    internal = state[1]
    _list(internal, 625, "RNG internal state")
    if len(internal) != 625:
        raise SnapshotError("RNG internal state must contain 625 integers")
    for word in internal[:-1]:
        _integer(word, "RNG word", minimum=0, maximum=2**32 - 1)
    _integer(internal[-1], "RNG index", minimum=0, maximum=624)
    cached = state[2]
    if cached is not None and (type(cached) is not float or not math.isfinite(cached)):
        raise SnapshotError("RNG Gaussian cache must be a finite float or null")
    return 3, tuple(internal), cached


def _references(refs, known, where):
    _list(refs, _MAX_CARDS, where)
    for ref in refs:
        _id(ref)
        if ref not in known:
            raise SnapshotError(f"unknown card ID in {where}")
    if len(set(refs)) != len(refs):
        raise SnapshotError(f"duplicate card ID in {where}")
    return set(refs)


def _validate(state):
    """Validate the full schema and graph before restoring any live objects."""
    _object(state, _ROOT_KEYS, "snapshot")
    if state["format"] != "rpg-card" or type(state["version"]) is not int or state["version"] != 1:
        raise SnapshotError("unsupported snapshot format or version (expected rpg-card version 1)")
    recipe = _recipe(state["deck"])
    _list(state["cards"], _MAX_CARDS, "cards")
    known = set()
    for row in state["cards"]:
        _object(row, {"id", "system", "suit", "number", "value", "orientation"}, "card")
        _id(row["id"])
        if row["id"] in known:
            raise SnapshotError("duplicate card ID in card table")
        known.add(row["id"])
        system = row["system"]
        if type(system) is not str or system not in _SYSTEMS:
            raise SnapshotError("unsupported card system")
        cls = _SYSTEMS[system]
        _integer(row["suit"], "card suit", minimum=0, maximum=len(cls.SUITS) - 1)
        ranks = cls.MINOR_NUMBERS if row["suit"] else cls.MAJOR_NUMBERS
        _integer(row["number"], "card number", minimum=0, maximum=len(ranks) - 1)
        if row["orientation"] not in ("upright", "reversed"):
            raise SnapshotError("orientation must be upright or reversed")
        _value(row["value"])
    placed = set()
    for zone in ("draw_pile", "discards", "drawn"):
        refs = _references(state[zone], known, zone)
        if placed & refs:
            raise SnapshotError("one card appears in more than one zone")
        placed.update(refs)
    if placed != known:
        raise SnapshotError("card table contains unplaced cards")
    hands = state["hands"]
    if type(hands) is not dict or len(hands) > _MAX_HANDS:
        raise SnapshotError(f"hands must be an object with at most {_MAX_HANDS} entries")
    held = set()
    drawn = set(state["drawn"])
    for name, refs in hands.items():
        _name(name)
        members = _references(refs, known, "hand")
        if held & members or not members <= drawn:
            raise SnapshotError("hand cards must be unique references into drawn cards")
        held.update(members)
    return (*recipe, _rng_state(state["rng"]))


def snapshot(deck, hands=None):
    """Return a detached, JSON-compatible snapshot of a deck and named hands.

    Include every occupied hand; unnamed empty hands need not be retained.
    Inconsistent ownership or unsupported types raise :class:`SnapshotError`.
    The caller owns storage and must prevent concurrent mutation during capture.
    """
    if type(deck) is not Deck:
        raise SnapshotError("only built-in Deck objects support snapshots")
    hands = {} if hands is None else hands
    if not isinstance(hands, Mapping) or len(hands) > _MAX_HANDS:
        raise SnapshotError(f"hands must be a mapping with at most {_MAX_HANDS} entries")
    if len(deck._owned) > _MAX_CARDS:
        raise SnapshotError(f"cards exceed limit {_MAX_CARDS}")
    _list(deck.cards, _MAX_CARDS, "draw pile")
    _list(deck.discards, _MAX_CARDS, "discards")
    if type(deck._out) is not dict or len(deck._out) > _MAX_CARDS:
        raise SnapshotError(f"drawn cards must have at most {_MAX_CARDS} entries")
    all_cards = deck.cards + deck.discards + list(deck._out)
    if any(type(card) not in _NAMES for card in all_cards):
        raise SnapshotError("only built-in card classes support snapshots")
    if (len(all_cards) != len(deck._owned) or len(set(all_cards)) != len(all_cards)
            or set(all_cards) != deck._owned):
        raise SnapshotError("live card zones must partition the owned inventory exactly once")
    if any(card._owner is not deck for card in all_cards):
        raise SnapshotError("card ownership does not match the deck")
    seen_hands, held = set(), set()
    named = {}
    for name, hand in hands.items():
        _name(name)
        if type(hand) is not Hand or hand.deck is not deck or hand in seen_hands:
            raise SnapshotError("named hands must be distinct hands belonging to this deck")
        seen_hands.add(hand)
        _list(hand.cards, _MAX_CARDS, "hand cards")
        members = []
        for card in hand.cards:
            if (type(card) not in _NAMES or card not in deck._out or card in held
                    or card._hand is not hand):
                raise SnapshotError("inconsistent live hand membership")
            held.add(card)
            members.append(card.card_id)
        named[name] = members
    if held != {card for card in all_cards if card._hand is not None}:
        raise SnapshotError("every occupied hand must be included in the snapshot")
    system = None if deck.card_system is None else _NAMES.get(deck.card_system)
    if deck.card_system is not None and system is None:
        raise SnapshotError("unsupported deck card system")
    mapping = deck._value_map
    if not isinstance(mapping, Mapping) or len(mapping) > _MAX_CARDS:
        raise SnapshotError(f"value_map must contain at most {_MAX_CARDS} entries")
    entries = []
    for key, value in mapping.items():
        if type(key) is int:
            suit, rank = None, key
        elif type(key) is tuple and len(key) == 2:
            suit, rank = key
            _integer(suit, "mapped suit", minimum=0)
            _integer(rank, "mapped rank", minimum=0)
        else:
            raise SnapshotError("value_map keys must be ranks or (suit, rank) pairs")
        entries.append({"suit": suit, "rank": rank, "value": _encode_value(value)})
    if type(deck._build_options) is not dict:
        raise SnapshotError("invalid builder options")
    if deck._rng is not random and type(deck._rng) is not random.Random:
        raise SnapshotError("only module random and ordinary random.Random support snapshots")
    rng = deck._rng.getstate()
    state = {
        "format": "rpg-card", "version": 1,
        "deck": {"system": system, "options": dict(deck._build_options), "value_map": entries},
        "cards": [{"id": card.card_id, "system": _NAMES[type(card)],
                   "suit": card.suit, "number": card.number,
                   "value": _encode_value(card.value), "orientation": card.orientation}
                  for card in all_cards],
        "draw_pile": [card.card_id for card in deck.cards],
        "discards": [card.card_id for card in deck.discards],
        "drawn": [card.card_id for card in deck._out],
        "hands": named,
        "rng": {"algorithm": "python.random.MT19937", "state": [rng[0], list(rng[1]), rng[2]]},
    }
    _validate(state)
    state["cards"].sort(key=lambda row: row["id"])
    return state


def restore(state):
    """Validate decoded JSON and return a new ``(deck, named_hands)`` pair.

    No file I/O, imports named by data, or changes to global random state occur.
    Card IDs survive restoration; Python object identities are new.
    """
    system, options, mapping, rng_state = _validate(state)
    rng = random.Random(0)
    rng.setstate(rng_state)
    deck = Deck(system, rng=rng, value_map=mapping)
    deck._build_options = options
    cards = {}
    for row in state["cards"]:
        card = _SYSTEMS[row["system"]](row["suit"], row["number"])
        card._card_id = row["id"]
        card.value = _value(row["value"])
        card.orientation = row["orientation"]
        cards[card.card_id] = card
    deck._adopt(cards.values())
    deck.cards.extend(cards[ref] for ref in state["draw_pile"])
    deck.discards.extend(cards[ref] for ref in state["discards"])
    deck._out = dict.fromkeys(cards[ref] for ref in state["drawn"])
    hands = {}
    for name, refs in state["hands"].items():
        hand = Hand(deck)
        hand.cards.extend(cards[ref] for ref in refs)
        for card in hand.cards:
            card._hand = hand
        hands[name] = hand
    return deck, hands
