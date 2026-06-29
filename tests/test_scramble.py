import numpy as np

from src.scramble import scramble, descramble


def test_reversible():
    bits = np.random.default_rng(1).integers(0, 2, 511).tolist()
    assert descramble(scramble(bits, 2026), 2026) == bits


def test_length_preserved():
    bits = [1, 0, 1, 1, 0]
    assert len(scramble(bits, 7)) == 5


def test_seed_changes_output():
    bits = [1] * 64
    assert scramble(bits, 1) != scramble(bits, 2)


def test_reproducible_with_fixed_seed():
    bits = ([1, 0, 1, 0, 1, 1] * 10)
    assert scramble(bits, 2026) == scramble(bits, 2026)


def test_breaks_long_runs():
    bits = [1] * 200
    scrambled = scramble(bits, 2026)
    # a constant input should not remain a constant run after scrambling
    assert 0 in scrambled and 1 in scrambled
