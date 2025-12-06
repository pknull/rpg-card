---
version: "1.0"
lastUpdated: "2025-12-06"
lifecycle: "active"
stakeholder: "pknull"
changeTrigger: "scope change, major milestone"
validatedBy: "human"
dependencies: []
---

# Project Brief: rpg-card

## Purpose

A Python library for creating and dealing cards for various RPG systems.

## Core Features

- Deck creation and shuffling
- Card dealing with configurable hand sizes
- Multiple card type implementations:
  - StandardCard (54-card deck)
  - TarotCard
  - ShadowCard
  - UnoCard

## Usage

```python
from card_picker import Deck, StandardCard

deck = Deck(StandardCard)
deck.create()
deck.shuffle()
hand = deck.deal(5)
```

## Technical Stack

- Language: Python
- Testing: pytest
- Installation: pip install -e .

## Project Structure

- `card_picker/` - Main library code
- `tests/` - Test suite
- `setup.py` - Package configuration

## Success Criteria

- Clean API for deck/card operations
- Support for multiple card types
- Well-tested codebase
