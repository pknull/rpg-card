# Decisions

- Preserve Deck(card_system), create(), shuffle(), deal(ncards=...) and exact
  legacy name strings for pk.asha. Legacy Uno remains 96 cards. Original tests
  stay intact; new builders provide alternate compositions explicitly.
- draw(n) returns physical card objects and fails atomically on insufficient
  cards; deal retains permissive short/negative-count behaviour. draw_until
  includes its match and consumes the remainder before raising on no match.
- Card values are independently configured exact rationals; rank indices stay
  zero-based. Orientation is assigned at shuffle and persists through transfers.
  Seeds/Random instances are supported; module random remains the default.
- Transfer methods enforce exclusive ownership and reject persistent-ID collisions
  before mutation. Return adopts unowned cards; remove/create release ownership.
  Combine/split move only remaining cards. Builder create retains composition
  and generates new IDs; composed decks cannot recreate. Split piles share their
  source RNG. Recall clears affected hands.
- Odds inspect the current remaining pile as a uniform sample, without mutation
  or RNG use. Return Fraction probabilities; no runtime probability dependency
  or game rules. Same-deck draws are dependent without replacement; separate-deck
  comparisons are independent. Replacement is an explicit option.
- Exact query limits: 10,000 cards per deck, 100 total draws, 100 predicates;
  default configurable max_work is 1,000,000 transitions/comparison pairs.
  Exceeding a bound raises OddsLimitError, never an approximation.
- Persistence is storage-neutral: snapshot(deck, named_hands) returns version-1
  JSON-compatible data; restore returns a new deck and named-hand mapping. Include
  every occupied hand. Preserve card IDs and full drawn order, including held
  cards. Restore uses a private RNG; never rewind global random or infer external
  shared-RNG relationships. Caller owns storage, authorization and atomic updates.
- Snapshots support built-in systems, module random and ordinary Random. Reject
  custom classes, unknown versions/fields, invalid ownership and malformed state;
  never pickle, dynamically import or repair data. Rational values use integer
  pairs. Bounds: 10,000 cards/map entries, 1,000 hands, 256-character names, 4,096-bit
  rational integers. Map indices must exist in the full underlying card system,
  including cards absent from a selected/depleted deck; unused invalid indices
  allowed by constructors are not serializable.
- Memory/ is exactly the v2 pair; .asha/config.json is tracked. Harness state,
  scratch reviews and logs stay local. A Room save is a checkpoint, not closure
  or permission to commit, push or tag.
