# RPG Card

Version 0.3.0: card objects, stateful decks and bounded exact draw probabilities
for RPG helpers. There are no runtime dependencies or encoded game rules.

## Installation and legacy usage

```bash
pip install -e .
```

```python
from card_picker import Deck, StandardCard

deck = Deck(StandardCard)  # initially empty, as before
deck.create()             # 54 cards, including two jokers
deck.shuffle()
names = deck.deal(5)       # unchanged list of display-name strings
```

`deal(ncards=1)` still takes from the end of `deck.cards`, returns fewer names
when exhausted, and returns `[]` for zero or negative counts. `create()` and
`shuffle()` still return `None`. Card names, suit ordering, zero-based `number`
indices and camelCase naming helpers are unchanged. The existing Uno deck is
still **96 cards**, not a conventional 108-card deck.

## Cards and builders

```python
from card_picker import Deck, TarotCard

standard = Deck.standard(jokers=False, seed=42)  # 52; default jokers=True gives 54
tarot = Deck.tarot()                           # 78
majors = Deck.tarot(arcana="major")             # 22
minors = Deck.tarot(arcana="minor")             # 56
shadow = Deck.shadow()                         # 78, historical Shadow names
uno = Deck.uno()                               # historical 96-card composition
custom = Deck.from_cards([TarotCard(0, 0), TarotCard(0, 10)])

card = majors.draw()[0]
print(card.name(), card.arcana, card.value, card.orientation)
```

Builders return populated decks. Calling `create()` again on a standard/tarot
builder preserves its selected composition (for example, 52 cards or majors
only). Cards expose:

| Attribute | Meaning |
|---|---|
| `suit` | Existing integer suit index; `SUITS[suit]` gives its label |
| `number`, `rank_index` | Existing zero-based rank/storage index |
| `value` | Exact numeric value, configurable independently of the name/index |
| `colour` | Standard suited cards: `"red"` or `"black"`; jokers: `None` |
| `arcana` | Tarot/Shadow: `"major"` or `"minor"`; other systems: `None` |
| `orientation` | `"upright"` or `"reversed"`; initially upright |
| `card_id` | Read-only UUID hex string identifying the physical card across saves |
| `name()` | Existing callable display-name method, not a string property |

Default values: standard Ace through King are 1–13, jokers 0; Tarot/Shadow
minors Ace through King are 1–14, majors 0–21. Uno digit cards use their
printed number, including duplicates; action and wild cards default to 0.
These are library defaults, not game scoring rules.

Pass `value_map` to a card constructor or deck builder. Keys are rank indices
or `(suit, rank_index)` pairs; a pair overrides a rank-only entry. Unspecified
cards retain their default value. Values must be `int` or `Fraction` (not bool
or float). For example:

```python
ace_high = Deck.standard(jokers=False, value_map={0: 14})
selected = TarotCard(1, 13, value_map={(1, 13): 20})
```

## Orientation and reproducibility

```python
import random

deck = Deck.tarot(arcana="major", rng=random.Random(123))
deck.shuffle()                           # each card upright with probability 1/2
deck.shuffle(upright_probability=0.75)    # independent orientations
deck.shuffle(upright_count=11)            # exactly 11; uniformly chosen subset
```

`upright_count` selects the fixed-count mode instead of probability mode.
Orientation stays with the physical card when drawing, returning, discarding,
splitting or combining; shuffling assigns it again. No orientation text is
added to legacy names.

Accept either `seed` or `rng`, not both. With neither, the library uses module
`random`, so `random.seed()` still reproduces runs. Card order is shuffled
before orientations are assigned. Orientation consumes extra random numbers:
historical multi-shuffle random streams are not promised to stay identical.
Queries through `Odds` never consume randomness.

## Deck state and hands

```python
from card_picker import Deck, DeckExhausted, Hand

deck = Deck.standard(seed=123)
deck.shuffle()
cards = deck.draw(3)             # card objects; tracked as drawn, not discarded
deck.discard(cards[:1])          # moves the first into deck.discards
deck.return_cards(cards[1:])     # first supplied card is the next drawn
top = deck.peek(2)               # top-first, non-mutating, truncated if necessary
deck.reshuffle()                 # mixes remaining cards and discards

hand = Hand(deck)
hand.draw(5)
played = hand.play(hand.cards[0]) # leaves hand, remains tracked as drawn
deck.discard([played])
hand.discard(hand.cards[:2])
deck.reshuffle(all_cards=True)   # also recalls drawn/dealt/held cards; clears hands
```

- `draw(n=1)` returns a list. If fewer than `n` cards remain, it raises
  `DeckExhausted` **without consuming any**. Zero returns `[]`; negative,
  noninteger and boolean sizes are rejected. `DeckExhausted` is a `ValueError`.
- `draw_until(predicate)` includes the matching card. If there is no match,
  it consumes the remaining pile then raises `DeckExhausted`; those cards
  remain tracked and can be recalled with `reshuffle(all_cards=True)`.
- `discard(cards)` accepts only this deck's drawn/held cards. `return_cards`
  accepts drawn, held, discarded or detached/unowned cards, but rejects cards
  owned by another deck. Batches reject duplicate identities and invalid
  transfers before mutation. `top=False` returns cards to the bottom, still
  in the supplied next-draw order.
- Returning/discarding a held card removes it from its hand. `create()` resets
  the deck and hands and releases ownership of old cards. Old card objects
  remain usable and can be explicitly adopted again.
- `reshuffle` accepts the same orientation options as `shuffle`. It validates
  those options against the resulting pile before moving any cards.
- Two identically named jokers are distinct physical cards. Cards are never
  deduplicated by name, rank or value.

Use the state methods for new code. `deck.cards` remains public for legacy
compatibility; direct list edits bypass ownership/state tracking. Do not mix
manual insertion/removal with state operations or hands. Card attributes are
also mutable; odds queries read their current values.

## Filtering, combining and splitting

```python
deck = Deck.standard(jokers=False)
removed = deck.remove(suit=1, rank=0)  # Ace of Hearts; filters intersect
deck.return_cards(removed)            # explicitly adopt the detached card again

combined = Deck.combine(Deck.standard(), Deck.standard())  # 108 physical cards
piles = Deck.tarot().split({
    "majors": lambda c: c.arcana == "major",
    "minors": lambda c: c.arcana == "minor",
})
```

`remove` also accepts `arcana` and `predicate`; it detaches matching remaining
cards and returns them. `combine` **moves**, rather than copies, remaining draw
piles. `split` transfers each remaining card into exactly one named pile;
missing or overlapping matches raise before any transfer. Source discards and
drawn/held cards stay with their source deck. Transfer preserves orientation.
Split piles share their source RNG stream. `combine` accepts its own `seed` or
`rng` (otherwise module `random`), rather than inheriting one source's RNG.
Composed decks (`from_cards`, `combine` and split results) have no rebuild
recipe: `create()` raises; use return/reshuffle to reuse their physical cards.

## Persistent decks and named hands

```python
import json
from card_picker import Deck, Hand, snapshot, restore

deck = Deck.standard(jokers=False, seed=42)
deck.shuffle()
hands = {"alice": Hand(deck), "bob": Hand(deck)}
hands["alice"].draw(5)
hands["bob"].draw(5)

# Store this JSON with the application's game ID.
payload = json.dumps(snapshot(deck, hands), allow_nan=False)

# A later command or a restarted process restores one consistent object graph.
deck, hands = restore(json.loads(payload))
played = hands["alice"].play(hands["alice"].cards[0])
deck.discard([played])
payload = json.dumps(snapshot(deck, hands), allow_nan=False)
```

`snapshot(deck, hands=None)` returns a detached, JSON-compatible dictionary.
`restore(state)` accepts that decoded dictionary and returns a **new deck and
name-to-Hand mapping**. Neither operation performs file or database I/O.

The snapshot includes every owned card, its stable ID, concrete built-in type,
rank/suit, exact value and orientation; draw-pile order; discards; all drawn
cards (held or not); named hands in hand order; the rebuild recipe/value map;
and the complete RNG state, including its Gaussian cache. Display names, colour
and arcana derive from the card system rather than being parsed or overridden.
Numeric card values use `[numerator, denominator]`, never floating point.

Include **every occupied hand** in the mapping. Missing occupied hands, aliases
for the same hand, foreign hands, duplicate IDs or inconsistent ownership raise
`SnapshotError` rather than silently dropping state. Empty hands survive when
explicitly named. Snapshot and restore do not mutate their inputs or consume
gameplay randomness. Take the snapshot while holding your application's lock.

Card IDs survive transfers and restoration, while Python object identities do
not. Use `card_id`, not display names or old object references, to identify a
card in a subsequent command. Two identically named jokers have different IDs.
Combining restored copies of the same cards, or returning a detached copy whose
ID already exists in the target deck, raises before mutation. To add a fresh
physical deck, use a builder instead of cloning a saved snapshot. `create()`
generates new cards and new IDs.

Restoration always creates a **private `random.Random`** loaded from the saved
state, even if the source used module `random`. It never rewinds global random
state. Continuation is reproducible under the same Python/library algorithms;
external decks sharing the source RNG are not part of this single-deck snapshot.

### Snapshot schema and validation

Schema version **1** has exactly these top-level fields:

| Field | Content |
|---|---|
| `format`, `version` | `"rpg-card"`, `1` |
| `deck` | `system`, explicit builder `options`, structured `value_map` entries |
| `cards` | Card records sorted by ID: `id`, `system`, `suit`, `number`, `value`, `orientation` |
| `draw_pile` | Card IDs in storage order, bottom to top |
| `discards` | Discard IDs in insertion order |
| `drawn` | All drawn/dealt IDs in insertion order, including held cards |
| `hands` | Hand names to ordered ID lists, referencing subsets of `drawn` |
| `rng` | `algorithm: "python.random.MT19937"`, JSON-list form of Python version-3 RNG state |

Supported systems are `standard`, `tarot`, `shadow` and `uno`; a composed
deck's recipe uses `system: null`, but every card retains its own system.
`options` is empty unless selecting standard `jokers` or tarot `arcana`.
Each value-map entry has `suit` (null for a rank-wide override), `rank` and
`value: [numerator, denominator]`. Composed recipes have empty options and maps.
Mapped indices must exist in the underlying full card system, even if the
corresponding cards are absent from the selected or depleted deck. Unused
out-of-range overrides accepted by the in-memory constructor are not serializable.

`restore` rejects unknown versions, fields or types; unknown/duplicate IDs;
unplaced or multiply placed cards; invalid hand links; non-rational card values;
and invalid RNG data with `SnapshotError`. Bounds apply to both operations:
**10,000 cards**, **1,000 hands**, **1–256 characters per hand name**,
**10,000 value-map entries**, and **4,096 bits per rational integer**.
RNG state has exactly 624 unsigned 32-bit words plus an index from 0 to 624.
Unsupported versions are rejected, not guessed or silently migrated.

Built-in decks/cards, module `random` and ordinary `random.Random` are supported.
Custom subclasses and `SystemRandom` are deliberately rejected by this API;
their extra behaviour cannot be safely inferred from a JSON record. No pickle,
dynamic class loading, executable callbacks or application metadata are stored.

The application owns game/player authorization, durable storage and concurrency.
Read-modify-write must be one locked transaction or use a revision-checked
compare-and-swap; otherwise two bot commands can both act on the same saved
card. Also impose input byte limits when parsing JSON. Keep snapshots private:
they contain the full deck order, every hand and future RNG state. This library
validates structure, not whether a player was authorized to change the data.

## Exact odds

```python
from fractions import Fraction
from card_picker import Deck, Odds

deck = Deck.standard(jokers=False)
odds = Odds(deck)
aces = odds.count(5, lambda c: c.rank_index == 0)
assert 1 - aces[0] == Fraction(18472, 54145)

suits = odds.counts(5, [lambda c, s=s: c.suit == s for s in range(1, 5)])
assert suits[2, 1, 1, 1] > 0
highest = odds.reading(2, kind="highest")
median = odds.reading(3, kind="kth", k=2)
total = odds.reading(3)  # sum; default projection is card.value
counts = odds.reading(3, kind="count", predicate=lambda c: c.colour == "red")
comparison = odds.compare()  # first single card against second from same pile
assert comparison == {"win": Fraction(8, 17), "tie": Fraction(1, 17),
                      "loss": Fraction(8, 17)}
```

Each query reads the **current remaining draw pile**, not the original deck or
discards. It models a uniform random sample of that pile, ignoring its known
top order; use `peek()` for deterministic top cards. An `Odds` object can be
reused after draws: its next query sees the changed pile. Queries do not mutate
deck state. Callbacks must be pure.

All probability values are `fractions.Fraction`. Impossible outcomes are
omitted, except `compare`, which always includes `win`, `tie` and `loss`.

- `count(n, predicate)` returns `{matching_count: probability}`.
- `counts(n, predicates)` returns `{count_tuple: probability}` in predicate
  order. Predicates may overlap. Disjoint exhaustive categories implement the
  multivariate hypergeometric distribution.
- `reading(n, kind="sum", value=None, k=None, predicate=None)` supports `sum`,
  `highest`, `lowest`, `kth` and `count`. `kth` is one-based, ascending. Numeric
  projections must return exact rationals (`int`/`Fraction`). `count` uses a
  predicate, not a numeric projection. Zero draws have sum/count zero; extrema
  and k-th readings require at least one card.
- `compare(n=1, other=None, other_n=None, kind="sum", other_kind=None,
  value=None, other_value=None, k=None, other_k=None)` compares two readings.
  Defaults reuse the left-hand options. `other=None` or the same deck means
  disjoint draws from one pile; another deck means independent samples.
  Count comparisons can use sum with `value=lambda c: int(condition(c))`.
- Every query accepts `replacement=True` for independent draws with return;
  otherwise sampling is without replacement. Replacement does not physically
  return cards or change the deck. Insufficient cards raise `DeckExhausted`.

### Exactness and limits

The engine groups identical projected attributes, then counts physical subsets
with binomial coefficients. Replacement uses multinomial weights. Dependent
comparisons allocate disjoint subsets jointly, rather than multiplying
independent marginal probabilities. No probability package is required.

Per-query hard bounds are **10,000 cards per deck**, **100 total draws** (both
sides combined for comparison) and **100 predicates**. The default work budget
is **1,000,000 dynamic-programming transitions/comparison pairs**. It can be
changed with `Odds(deck, max_work=...)`. Requests exceeding a bound raise
`OddsLimitError`, whose message names the bound and value. A request inside the
card/draw bounds can still exceed the work budget, especially with many
distinct projected values. There is no silent truncation or approximate fallback.

## Tests

```bash
python -m pytest -q
```

Tests cover the approved rpg-skills fixtures, independent brute-force
enumeration on small physical decks (including duplicate values and replacement),
and fixed-seed dealing against exact probabilities within six binomial standard
errors. They also retain the original regression suite and check complete
legacy name lists. Statistical checks supplement, not replace, exact checks.
