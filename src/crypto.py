from __future__ import annotations

import numpy as np


def _pn_sequence(length: int, seed: int = 2026) -> list[int]:
    rng = np.random.default_rng(seed)
    return [int(x) for x in rng.integers(0, 2, size=length)]


def scramble(bits: list[int], seed: int = 2026) -> list[int]:
    pn = _pn_sequence(len(bits), seed)
    return [int(bit) ^ pn_bit for bit, pn_bit in zip(bits, pn)]


def descramble(bits: list[int], seed: int = 2026) -> list[int]:
    return scramble(bits, seed=seed)


encrypt = scramble
decrypt = descramble
scramble_bits = scramble
descramble_bits = descramble

