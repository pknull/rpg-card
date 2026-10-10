"""Persistence must work across an actual process boundary, not just objects."""

import json
from pathlib import Path
import random
import subprocess
import sys

from card_picker import Deck, Hand, snapshot


def test_fresh_process_resumes_cards_hands_and_randomness(tmp_path):
    rng = random.Random(884)
    rng.gauss(0, 1)  # Include a populated Gaussian cache in the RNG state.
    deck = Deck.tarot(rng=rng)
    deck.shuffle()
    hands = {"a": Hand(deck), "b": Hand(deck), "empty": Hand(deck)}
    hands["a"].draw(3)
    deck.draw(2)
    hands["b"].draw(4)
    deck.discard(deck.draw(2))
    payload = json.dumps(snapshot(deck, hands), allow_nan=False)
    root = str(Path(__file__).resolve().parents[1])
    continuation = """
hands['a'].draw(2)
card = hands['b'].play(hands['b'].cards[1])
deck.discard([card])
deck.reshuffle(all_cards=True, upright_count=17)
hands['a'].draw(5)
hands['b'].draw(5)
"""
    program = (
        f"import sys, json; sys.path.insert(0, {root!r})\n"
        "from card_picker import restore, snapshot\n"
        "deck, hands = restore(json.loads(sys.stdin.read()))\n"
        + continuation + "print(json.dumps(snapshot(deck, hands), allow_nan=False))\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", program], input=payload,
        cwd=tmp_path, capture_output=True, text=True, check=True, timeout=10,
    )
    exec(continuation, {"deck": deck, "hands": hands})
    assert json.loads(result.stdout) == snapshot(deck, hands)
