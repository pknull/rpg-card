# RPG Card

A small library for creating and dealing cards for various RPG systems.

## Installation

```bash
pip install -e .
```

## Usage

```python
from card_picker import Deck, StandardCard

# Build a standard 54 card deck
deck = Deck(StandardCard)
deck.create()
deck.shuffle()

# Deal five cards
hand = deck.deal(5)
print(hand)
```

The module also includes `TarotCard`, `ShadowCard`, and `UnoCard` implementations.

## Running tests

The project uses `pytest` for tests:

```bash
pytest
```
