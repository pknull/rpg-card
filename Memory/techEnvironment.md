---
version: "1.0"
lastUpdated: "2025-12-06"
lifecycle: "active"
stakeholder: "pknull"
changeTrigger: "tool change, convention discovery"
validatedBy: "human"
dependencies: []
---

# Technical Environment: rpg-card

## Language & Runtime

- **Language**: Python
- **Package Manager**: pip
- **Testing**: pytest

## Project Structure

```
rpg-card/
├── card_picker/       # Main library
├── tests/             # Test suite
├── setup.py           # Package config
├── README.md
├── Memory/            # Asha Memory Bank
└── CLAUDE.md
```

## Installation

```bash
pip install -e .
```

## Testing

```bash
pytest
```

## Key Classes

- `Deck` - Deck management (create, shuffle, deal)
- `StandardCard` - 54-card standard deck
- `TarotCard` - Tarot deck implementation
- `ShadowCard` - Shadow deck implementation
- `UnoCard` - Uno deck implementation
