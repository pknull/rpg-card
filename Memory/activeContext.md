# Objective

Provide persistent card/hand state and bounded exact RPG draw probabilities,
without game rules, storage backends or runtime probability dependencies.

# State

Verified 2026-10-10. Release commit 1113d95 and annotated tag v0.3.0 were
pushed to github.com/pknull/rpg-card with Keeper authorization. Remote peeled
tag verified at 1113d9569c8fb1af28e28ee4a0b5da0496fab3dd.
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
Package metadata and __version__ both declare 0.3.0. No bot dependency pins or
deployments were changed. This remains an ongoing project Room.

Save checkpoint reverified all 300 tests and remote master at ccd434e (the
release-publication Memory commit). Existing bots need no changes for their
current functionality: pk.asha still pins ceace06 and uses the legacy deal API;
pk.zalgo has no rpg-card requirement. New features require deliberate consumer
integration, with caller-owned storage and atomic updates for persistent games.

# Next

- Consumer dependency updates and persistent-game integration belong to their
  respective projects and require separate direction.

# Blockers

- None.
