# Objective

Provide persistent card/hand state and bounded exact RPG draw probabilities,
without game rules, storage backends or runtime probability dependencies.

# State

Verified 2026-10-09. Base HEAD a3f2413; v0.3.0 implementation is uncommitted.
Approved requirements are implemented: structured attributes, deck builders,
orientation, seeding, physical-card ownership, hands and Fraction odds. Legacy
deal() names/behaviour and original tests remain unchanged.

Keeper-approved persistence extension adds snapshot(deck, hands), restore(state),
SnapshotError and stable card_id values. Version-1 JSON state preserves all
zones, named hands, exact values, rebuild options and RNG continuation. Restore
creates fresh objects and a private RNG without changing module random. Built-in
systems are supported; unsupported custom classes and invalid graphs are rejected.
README documents schema, limits and caller-owned storage/concurrency boundaries.

Tests were red first. Final suite: 300 passed, including every original odds
fixture and a fresh-process JSON continuation test. Correctness/input-validation
reviews passed after fix reviews. Eight README examples and an isolated offline
wheel smoke pass; no runtime dependencies. Tests use .venv Python; wheel build
uses system python3 because .venv lacks setuptools. Deployed bots were not run.
No commit, push or tag was performed. This remains an ongoing project Room.

# Next

- Keeper local review of the uncommitted v0.3.0 implementation and persistence API.
- Commit, push or tag only on separate Keeper direction.

# Blockers

- None.
