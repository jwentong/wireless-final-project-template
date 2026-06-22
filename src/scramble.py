from __future__ import annotations

import numpy as np


def _clean_bits(bits) -> np.ndarray:
    return np.array([1 if int(bit) else 0 for bit in list(bits)], dtype=np.uint8)


def scramble(bits, seed: int = 2026) -> list[int]:
    arr = _clean_bits(bits)
    if arr.size == 0:
        return []
    rng = np.random.default_rng(seed)
    pn = rng.integers(0, 2, size=arr.size, dtype=np.uint8)
    return np.bitwise_xor(arr, pn).astype(int).tolist()


def descramble(bits, seed: int = 2026) -> list[int]:
    return scramble(bits, seed=seed)


scramble_bits = scramble
descramble_bits = descramble
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble
