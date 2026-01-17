---
version: "1.1"
lastUpdated: "2026-01-16"
lifecycle: "active"
stakeholder: "pknull"
changeTrigger: "session end"
validatedBy: "system"
dependencies: ["projectbrief.md"]
---

# Active Context: rpg-card

## Current Focus

Bug fixes implemented based on code audit review.

## Recent Changes

- Project onboarded to Asha framework (2025-12-06)

## Session Notes

### 2026-01-16: Audit Review Implementation

**Goal:** Review AUDIT-REVIEW.md findings and implement fixes for identified bugs.

**Accomplished:**
1. Set up pytest infrastructure (created `.venv`, installed pytest)
2. Created comprehensive baseline tests (`tests/test_baseline.py`, 41 tests) documenting existing behavior
3. Implemented all critical and high-priority fixes:
   - **UnoCard.name() fix** (`Card.py:208-213`): Override `name()` to produce "Red Zero" instead of "ZeroRed "
   - **TarotCard Death card** (`Card.py:87`): Added missing "Death" to MAJOR_NUMBERS (deck now 78 cards)
   - **Input validation** (`Card.py:8-26`): Added bounds checking in `BaseCard.__init__()` to prevent negative index exploitation
4. Updated tests to verify correct behavior (47 tests, all passing)

**Key Learnings:**
- Baseline tests documenting buggy behavior before fixes enables confident refactoring
- Python negative indexing can silently produce wrong results without validation
- UnoCard naming convention differs from other cards (color before number)

## Next Steps

- Consider low-priority items from audit:
  - Add type hints to codebase
  - Migrate setup.py to pyproject.toml
  - Document expected deck sizes in docstrings

## Open Questions

- Is `Deck.deal()` returning strings (card names) instead of Card objects intentional?
- Should there be a way to return cards to deck or reset without `create()`?

## Blockers

- None
