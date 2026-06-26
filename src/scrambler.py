"""PN XOR scrambling."""

from __future__ import annotations

import numpy as np


def generate_pn_sequence(length: int, seed: int) -> list[int]:
    """Generate a deterministic pseudo-noise bit sequence."""
    rng = np.random.default_rng(seed)
    return [int(bit) for bit in rng.integers(0, 2, size=length, dtype=np.uint8)]


def scramble_bits(bits: list[int], seed: int = 2026) -> list[int]:
    """Scramble bits by XORing with a seed-controlled PN sequence."""
    pn = generate_pn_sequence(len(bits), seed)
    return [int(bit) ^ pn_bit for bit, pn_bit in zip(bits, pn)]


def descramble_bits(bits: list[int], seed: int = 2026) -> list[int]:
    """Descramble bits. XOR scrambling is self-inverse."""
    return scramble_bits(bits, seed=seed)


scramble = scramble_bits
descramble = descramble_bits
