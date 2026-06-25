import numpy as np


def _pn_sequence(length, seed=2026):
    rng = np.random.default_rng(int(seed))
    return rng.integers(0, 2, size=int(length), dtype=np.uint8)


def scramble(bits, seed=2026):
    bit_array = np.array([int(bit) for bit in bits], dtype=np.uint8)
    pn = _pn_sequence(len(bit_array), seed)
    return np.bitwise_xor(bit_array, pn).astype(int).tolist()


def descramble(bits, seed=2026):
    return scramble(bits, seed=seed)


scramble_bits = scramble
descramble_bits = descramble
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble

