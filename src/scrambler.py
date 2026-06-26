import numpy as np


def _pn(length, seed=2026):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=length, dtype=np.uint8)


def scramble(bits, seed=2026):
    arr = np.asarray(bits, dtype=np.uint8) & 1
    return np.bitwise_xor(arr, _pn(len(arr), seed)).astype(int).tolist()


def descramble(bits, seed=2026):
    return scramble(bits, seed=seed)


scramble_bits = scramble
descramble_bits = descramble
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble

