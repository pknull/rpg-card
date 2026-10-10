"""Version-one JSON snapshots preserve physical cards, zones, hands and RNG."""

from copy import deepcopy
from fractions import Fraction
import json
import random
import re

import pytest

import card_picker as cp


def ids(cards):
    return [card.card_id for card in cards]


def json_copy(value):
    return json.loads(json.dumps(value, allow_nan=False))


def literal_state():
    """Independent schema fixture; no production snapshot helpers are used."""
    return {
        'format': 'rpg-card', 'version': 1,
        'deck': {'system': 'standard', 'options': {'jokers': False}, 'value_map': []},
        'cards': [
            {'id': '0' * 31 + '1', 'system': 'standard', 'suit': 1, 'number': 0,
             'value': [1, 1], 'orientation': 'upright'},
            {'id': '0' * 31 + '2', 'system': 'standard', 'suit': 2, 'number': 1,
             'value': [2, 1], 'orientation': 'reversed'},
        ],
        'draw_pile': ['0' * 31 + '1'], 'discards': [], 'drawn': ['0' * 31 + '2'],
        'hands': {'keeper': ['0' * 31 + '2']},
        'rng': {'algorithm': 'python.random.MT19937', 'state': json_copy(random.Random(912).getstate())},
    }


def test_card_ids_are_unique_read_only_and_stable_through_moves():
    """Fails if IDs identify names instead of physical cards, mutate, or change on transfer."""
    deck = cp.Deck.standard(seed=17)
    original = ids(deck.cards)
    assert len(set(original)) == 54
    assert all(re.fullmatch(r'[0-9a-f]{32}', value) for value in original)
    jokers = [c for c in deck.cards if c.suit == 0]
    assert jokers[0].name() == jokers[1].name() == 'Joker'
    assert jokers[0].card_id != jokers[1].card_id
    with pytest.raises(AttributeError):
        jokers[0].card_id = 'f' * 32
    deck.shuffle()
    cards = deck.draw(5)
    deck.discard(cards)
    deck.reshuffle(all_cards=True)
    combined = cp.Deck.combine(deck)
    assert set(ids(combined.cards)) == set(original)


@pytest.mark.parametrize('builder,kwargs,size,system,options', [
    ('standard', {}, 54, 'standard', {}),
    ('standard', {'jokers': False}, 52, 'standard', {'jokers': False}),
    ('tarot', {}, 78, 'tarot', {}),
    ('tarot', {'arcana': 'major'}, 22, 'tarot', {'arcana': 'major'}),
    ('tarot', {'arcana': 'minor'}, 56, 'tarot', {'arcana': 'minor'}),
    ('shadow', {}, 78, 'shadow', {}),
    ('uno', {}, 96, 'uno', {}),
])
def test_builtin_json_roundtrips_and_rebuild_recipes(builder, kwargs, size, system, options):
    """Fails if JSON loses attributes, order, IDs, builder composition, or card classes."""
    deck = getattr(cp.Deck, builder)(seed=221, **kwargs)
    deck.shuffle()
    state = cp.snapshot(deck)
    assert set(state) == {'format', 'version', 'deck', 'cards', 'draw_pile', 'discards', 'drawn', 'hands', 'rng'}
    assert state['format'] == 'rpg-card' and state['version'] == 1
    assert state['deck'] == {'system': system, 'options': options, 'value_map': []}
    assert [row['id'] for row in state['cards']] == sorted(ids(deck.cards))
    assert state['draw_pile'] == ids(deck.cards)
    restored, hands = cp.restore(json_copy(state))
    assert hands == {}
    assert cp.snapshot(restored) == state
    assert restored is not deck
    assert all(a is not b and type(a) is type(b) and a.name() == b.name()
               for a, b in zip(deck.cards, restored.cards))
    assert ids(restored.draw(5)) == ids(deck.draw(5))
    restored.create()
    assert len(restored) == size
    assert not set(ids(restored.cards)) & {row['id'] for row in state['cards']}


def test_snapshot_handles_all_zones_hands_and_out_insertion_order():
    """Fails if held cards duplicate zones or named-hand order changes recalled draw order."""
    deck = cp.Deck.standard(seed=409)
    alice, bob, empty = cp.Hand(deck), cp.Hand(deck), cp.Hand(deck)
    unheld = deck.draw(1)
    alice_cards = alice.draw(2)
    discarded = deck.draw(1)
    bob_cards = bob.draw(2)
    played = alice.play(alice_cards[0])
    deck.discard(discarded)
    named = {'bob': bob, 'empty': empty, 'alice': alice}
    state = cp.snapshot(deck, named)
    assert state['drawn'] == ids(unheld + alice_cards + bob_cards)
    assert state['hands'] == {'bob': ids(bob_cards), 'empty': [], 'alice': ids(alice_cards[1:])}
    assert state['discards'] == ids(discarded)
    restored, hands = cp.restore(json_copy(state))
    assert cp.snapshot(restored, hands) == state
    assert all(hand.deck is restored for hand in hands.values())
    assert hands['empty'].cards == []
    assert hands['alice'].play(hands['alice'].cards[0]).card_id == alice_cards[1].card_id
    # Restore again so both continuations begin with identical hand links.
    restored, hands = cp.restore(json_copy(state))
    deck.reshuffle(all_cards=True, upright_count=17)
    restored.reshuffle(all_cards=True, upright_count=17)
    assert cp.snapshot(restored, hands) == cp.snapshot(deck, named)
    assert played.card_id in ids(deck.cards)
    assert all(not hand.cards for hand in hands.values())


def test_depleted_deck_restores_unheld_cards_and_discards():
    """Fails if an empty draw pile is mistaken for an empty owned-card inventory."""
    deck = cp.Deck.tarot(arcana='major', seed=12)
    cards = deck.draw(22)
    deck.discard(cards[:11])
    state = cp.snapshot(deck)
    restored, hands = cp.restore(json_copy(state))
    assert len(restored) == 0 and hands == {}
    assert ids(restored.discards) == ids(cards[:11])
    restored.reshuffle(all_cards=True)
    deck.reshuffle(all_cards=True)
    assert cp.snapshot(restored) == cp.snapshot(deck)


def test_mixed_composed_decks_and_duplicate_jokers_roundtrip():
    """Fails if restore chooses one card system for a mixed deck or merges equal names."""
    deck = cp.Deck.combine(cp.Deck.standard(), cp.Deck.tarot(arcana='major'), cp.Deck.uno(), cp.Deck.shadow(), seed=712)
    state = cp.snapshot(deck)
    assert state['deck'] == {'system': None, 'options': {}, 'value_map': []}
    restored, _ = cp.restore(json_copy(state))
    assert cp.snapshot(restored) == state
    assert len({c.card_id for c in restored.cards}) == 250
    assert {type(c) for c in restored.cards} == {cp.StandardCard, cp.TarotCard, cp.UnoCard, cp.ShadowCard}
    with pytest.raises(ValueError):
        restored.create()


def test_fraction_values_and_mapping_survive_json_and_create():
    """Fails if rational values round through floats or rank-specific mapping precedence is lost."""
    deck = cp.Deck.standard(jokers=False, seed=53, value_map={0: 14, (1, 0): Fraction(-29, 2)})
    deck.cards[-1].value = Fraction(5, 7)
    state = cp.snapshot(deck)
    assert sorted(state['deck']['value_map'], key=lambda row: row['suit'] is not None) == [
        {'suit': None, 'rank': 0, 'value': [14, 1]},
        {'suit': 1, 'rank': 0, 'value': [-29, 2]},
    ]
    assert next(row for row in state['cards'] if row['id'] == deck.cards[-1].card_id)['value'] == [5, 7]
    restored, _ = cp.restore(json_copy(state))
    assert restored.cards[-1].value == Fraction(5, 7)
    restored.create()
    aces = {c.suit: c.value for c in restored.cards if c.number == 0}
    assert aces == {1: Fraction(-29, 2), 2: 14, 3: 14, 4: 14}


def test_snapshot_is_independent_and_does_not_consume_rng_or_mutate_source():
    """Fails if exported containers alias live state or snapshot advances RNG."""
    rng = random.Random(642)
    deck = cp.Deck.standard(rng=rng)
    hand = cp.Hand(deck)
    hand.draw(2)
    before = list(deck.cards), list(hand.cards), rng.getstate()
    state = cp.snapshot(deck, {'h': hand})
    assert (deck.cards, hand.cards, rng.getstate()) == before
    original = deepcopy(state)
    state['draw_pile'].clear()
    state['hands']['h'].clear()
    state['cards'][0]['value'][0] = 998
    state['rng']['state'][1][0] = 0
    assert cp.snapshot(deck, {'h': hand}) == original


def test_module_rng_restore_never_rewinds_global_random_and_preserves_gauss_cache():
    """Fails if restore calls global setstate or drops the cached Gaussian sample."""
    previous = random.getstate()
    try:
        random.seed(875)
        random.gauss(0, 1)
        deck = cp.Deck.standard()
        state = cp.snapshot(deck)
        assert state['rng']['state'][2] is not None
        restored, _ = cp.restore(json_copy(state))
        assert cp.snapshot(restored) == state
        assert json_copy(random.getstate()) == state['rng']['state']
        random.random()
        global_before = random.getstate()
        another, _ = cp.restore(json_copy(state))
        assert random.getstate() == global_before
        restored.shuffle()
        another.shuffle()
        assert cp.snapshot(restored) == cp.snapshot(another)
        assert random.getstate() == global_before
    finally:
        random.setstate(previous)


def test_restore_accepts_literal_schema_and_never_mutates_input():
    """Fails if decoder requires in-process snapshot objects or mutates input containers."""
    state = literal_state()
    before = deepcopy(state)
    deck, hands = cp.restore(state)
    assert state == before
    assert deck.draw()[0].name() == 'Ace of Hearts'
    held = hands['keeper'].cards[0]
    assert held.name() == 'Two of Spades' and held.orientation == 'reversed'
    assert held.card_id == '0' * 31 + '2'
    hands['keeper'].discard([held])
    assert state == before


@pytest.mark.parametrize('which', ['omitted', 'duplicate_name', 'foreign', 'bad_name', 'non_hand'])
def test_snapshot_rejects_missing_duplicate_or_foreign_hands(which):
    """Fails if snapshot silently loses active hands or accepts ambiguous hand ownership."""
    deck = cp.Deck.standard(seed=1)
    hand = cp.Hand(deck)
    hand.draw(2)
    hands = {
        'omitted': {}, 'duplicate_name': {'a': hand, 'b': hand},
        'foreign': {'a': hand, 'b': cp.Hand(cp.Deck.standard())},
        'bad_name': {'': hand}, 'non_hand': {'a': hand, 'b': []},
    }[which]
    before = list(deck.cards), list(hand.cards), deck._rng.getstate()
    with pytest.raises(cp.SnapshotError):
        cp.snapshot(deck, hands)
    assert (deck.cards, hand.cards, deck._rng.getstate()) == before


@pytest.mark.parametrize('corruption', [
    'duplicate_id', 'invalid_id', 'duplicate_draw', 'orphan', 'foreign_owner',
    'cross_zone', 'hand_not_out', 'missing_hand_link', 'wrong_hand_link',
    'bad_orientation', 'bad_value', 'huge_value', 'bad_rank',
])
def test_snapshot_rejects_incoherent_live_card_state(corruption):
    """Fails if manual list/attribute corruption is silently published as valid state."""
    deck = cp.Deck.standard(seed=99)
    hand = cp.Hand(deck)
    held = hand.draw(1)[0]
    first = deck.cards[0]
    if corruption == 'duplicate_id':
        first._card_id = deck.cards[1].card_id
    elif corruption == 'invalid_id':
        first._card_id = 'not-an-id'
    elif corruption == 'duplicate_draw':
        deck.cards.append(first)
    elif corruption == 'orphan':
        deck.cards.remove(first)
    elif corruption == 'foreign_owner':
        first._owner = None
    elif corruption == 'cross_zone':
        deck.discards.append(first)
    elif corruption == 'hand_not_out':
        del deck._out[held]
    elif corruption == 'missing_hand_link':
        held._hand = None
    elif corruption == 'wrong_hand_link':
        held._hand = cp.Hand(deck)
    elif corruption == 'bad_orientation':
        first.orientation = 'sideways'
    elif corruption == 'bad_value':
        first.value = 1.5
    elif corruption == 'huge_value':
        first.value = 1 << 4096
    elif corruption == 'bad_rank':
        first.number = True
    before = list(deck.cards), list(deck.discards), list(deck._out), list(hand.cards), deck._rng.getstate()
    with pytest.raises(cp.SnapshotError):
        cp.snapshot(deck, {'h': hand})
    assert (deck.cards, deck.discards, list(deck._out), hand.cards, deck._rng.getstate()) == before


def test_snapshot_rejects_custom_types_and_nonstandard_rngs():
    """Fails if persistence permits arbitrary class imports or unsupported RNG state."""
    class CustomCard(cp.StandardCard):
        pass

    class CustomRandom(random.Random):
        pass

    for deck in (cp.Deck.from_cards([CustomCard(1, 0)]),
                 cp.Deck.standard(rng=random.SystemRandom()),
                 cp.Deck.standard(rng=CustomRandom(1))):
        with pytest.raises(cp.SnapshotError):
            cp.snapshot(deck)


@pytest.mark.parametrize('path,value', [
    (('format',), 'pickle'), (('version',), 2), (('version',), True),
    (('deck', 'system'), 'custom.module.Card'), (('deck', 'options'), {'unknown': 1}),
    (('deck', 'options'), {'jokers': 0}), (('deck', 'value_map'), [{'suit': None, 'rank': True, 'value': [1, 1]}]),
    (('cards', 0, 'id'), 'x' * 32), (('cards', 0, 'id'), 1),
    (('cards', 0, 'system'), '__import__'), (('cards', 0, 'suit'), True),
    (('cards', 0, 'suit'), 8), (('cards', 0, 'number'), -1),
    (('cards', 0, 'number'), 13), (('cards', 0, 'number'), 1.0),
    (('cards', 0, 'value'), [1, 0]), (('cards', 0, 'value'), [True, 1]),
    (('cards', 0, 'value'), [1, 1.5]), (('cards', 0, 'value'), [1 << 4096, 1]),
    (('cards', 0, 'value'), [1]), (('cards', 0, 'orientation'), 'sideways'),
    (('draw_pile',), ['f' * 32]), (('draw_pile',), ['0' * 31 + '1'] * 2),
    (('discards',), ['0' * 31 + '1']), (('drawn',), []),
    (('hands',), {'h': ['0' * 31 + '1']}),
    (('hands',), {'a': ['0' * 31 + '2'], 'b': ['0' * 31 + '2']}),
    (('hands',), {'h': ['0' * 31 + '2'] * 2}), (('hands',), {'': []}),
    (('hands',), {'x' * 257: []}), (('hands',), {1: []}),
    (('rng', 'algorithm'), 'custom'), (('rng', 'state'), [2, [], None]),
    (('rng', 'state', 0), True), (('rng', 'state', 1), [0] * 624),
    (('rng', 'state', 1, 0), True), (('rng', 'state', 1, 0), -1),
    (('rng', 'state', 1, 0), 1 << 32), (('rng', 'state', 1, 624), 625),
    (('rng', 'state', 2), float('nan')), (('rng', 'state', 2), float('inf')),
    (('rng', 'state', 2), True),
])
def test_restore_rejects_malformed_schema_atomically(path, value):
    """Fails if malformed data coerces booleans/numbers or bypasses schema/zone checks."""
    state = literal_state()
    target = state
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    before = deepcopy(state)
    global_before = random.getstate()
    with pytest.raises(cp.SnapshotError):
        cp.restore(state)
    # NaN is intentionally nonreflexive, so compare serialized data instead.
    assert repr(state) == repr(before)
    assert random.getstate() == global_before


@pytest.mark.parametrize('section', [None, 'deck', 'card', 'rng'])
def test_restore_rejects_unknown_fields(section):
    """Fails if unknown fields are silently ignored instead of enforcing versioned schema."""
    state = literal_state()
    target = state if section is None else state['cards'][0] if section == 'card' else state[section]
    target['unknown'] = 'payload'
    with pytest.raises(cp.SnapshotError):
        cp.restore(state)


@pytest.mark.parametrize('change', ['duplicate_table', 'orphan_table', 'missing_field', 'composed_options', 'composed_mapping', 'duplicate_mapping'])
def test_restore_rejects_duplicate_or_orphan_records_and_invalid_recipes(change):
    """Fails if table identity or rebuild recipe validation permits ambiguity."""
    state = literal_state()
    if change == 'duplicate_table':
        state['cards'].append(deepcopy(state['cards'][0]))
    elif change == 'orphan_table':
        extra = deepcopy(state['cards'][0])
        extra['id'] = 'f' * 32
        state['cards'].append(extra)
    elif change == 'missing_field':
        del state['cards'][0]['value']
    elif change == 'composed_options':
        state['deck']['system'] = None
    elif change == 'composed_mapping':
        state['deck'] = {'system': None, 'options': {}, 'value_map': [{'suit': None, 'rank': 0, 'value': [1, 1]}]}
    else:
        entry = {'suit': None, 'rank': 0, 'value': [1, 1]}
        state['deck']['value_map'] = [entry, deepcopy(entry)]
    with pytest.raises(cp.SnapshotError):
        cp.restore(state)


def test_snapshot_and_restore_enforce_card_and_hand_bounds():
    """Fails if persistence accepts oversized collections beyond documented limits."""
    huge = cp.Deck.from_cards([cp.StandardCard(1, 0) for _ in range(10001)], seed=1)
    with pytest.raises(cp.SnapshotError, match='10.?000'):
        cp.snapshot(huge)
    deck = cp.Deck.from_cards([], seed=2)
    hands = {str(i): cp.Hand(deck) for i in range(1001)}
    with pytest.raises(cp.SnapshotError, match='1.?000'):
        cp.snapshot(deck, hands)
    state = literal_state()
    state['hands'] = {str(i): [] for i in range(1001)}
    with pytest.raises(cp.SnapshotError, match='1.?000'):
        cp.restore(state)
    state = literal_state()
    row = state['cards'][0]
    state['cards'] = [dict(row, id=f'{i:032x}') for i in range(10001)]
    state['draw_pile'] = [row['id'] for row in state['cards']]
    state['drawn'] = []
    state['hands'] = {}
    with pytest.raises(cp.SnapshotError, match='10.?000'):
        cp.restore(state)


def test_valid_boundary_hand_names_and_fraction_sizes():
    """Fails if maximum valid hand-name/rational sizes are rejected by off-by-one checks."""
    card = cp.StandardCard(1, 0, value_map={0: Fraction((1 << 4096) - 1, 2)})
    deck = cp.Deck.from_cards([card], seed=0)
    hands = {'x' * 256: cp.Hand(deck)}
    state = cp.snapshot(deck, hands)
    restored, restored_hands = cp.restore(json_copy(state))
    assert cp.snapshot(restored, restored_hands) == state
    with pytest.raises(cp.SnapshotError):
        cp.snapshot(deck, {'x' * 257: hands['x' * 256]})


def test_combine_rejects_restored_duplicate_ids_before_moving_either_source():
    """Fails if combine permits distinct objects with duplicate persistent physical IDs."""
    source = cp.Deck.standard(seed=101)
    clone, _ = cp.restore(json_copy(cp.snapshot(source)))
    before_source, before_clone = cp.snapshot(source), cp.snapshot(clone)
    with pytest.raises(ValueError):
        cp.Deck.combine(source, clone)
    assert cp.snapshot(source) == before_source
    assert cp.snapshot(clone) == before_clone


def test_return_rejects_detached_restored_clone_id_atomically():
    """Fails if adoption accepts an ID already present in any target zone."""
    source = cp.Deck.standard(seed=12)
    clone, _ = cp.restore(json_copy(cp.snapshot(source)))
    detached = clone.remove(suit=1, rank=0)
    before_source, before_clone = cp.snapshot(source), cp.snapshot(clone)
    fresh = cp.StandardCard(2, 0)
    with pytest.raises(ValueError):
        source.return_cards([fresh] + detached)
    assert cp.snapshot(source) == before_source
    assert cp.snapshot(clone) == before_clone
    adopted = cp.Deck.from_cards([fresh] + detached)
    assert len(adopted) == 2


@pytest.mark.parametrize('value', [None, [], 'serialized json', 1, True])
def test_restore_requires_decoded_dict(value):
    """Fails if restore accepts ambiguous text or nonobject roots."""
    with pytest.raises(cp.SnapshotError):
        cp.restore(value)
