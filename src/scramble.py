"""Reversible PN-sequence scrambling."""

from __future__ import annotations

from typing import Iterable, List

import numpy as np


def _as_bits(bits: Iterable[int]) -> np.ndarray:
    return np.asarray([1 if int(bit) else 0 for bit in bits], dtype=np.uint8)


def scramble(bits: Iterable[int], seed: int = 2026) -> List[int]:
    """XOR bits with a reproducible pseudo-noise sequence."""
    bit_array = _as_bits(bits)
    rng = np.random.default_rng(int(seed))
    pn = rng.integers(0, 2, size=bit_array.size, dtype=np.uint8)
    return np.bitwise_xor(bit_array, pn).astype(int).tolist()


def descramble(bits: Iterable[int], seed: int = 2026) -> List[int]:
    """Descrambling is identical to scrambling for XOR PN sequences."""
    return scramble(bits, seed=seed)


scramble_bits = scramble
descramble_bits = descramble
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble

