"""Scramble / descramble module using XOR with PN sequence."""

import numpy as np


def scramble(bits: list[int], seed: int = 2026) -> list[int]:
    """Scramble bits by XOR-ing with a PN sequence from a seeded RNG.

    Args:
        bits: Input bits (list of 0/1 ints).
        seed: Random seed for reproducibility.

    Returns:
        Scrambled bits (same length).
    """
    rng = np.random.default_rng(seed)
    pn = (rng.random(len(bits)) > 0.5).astype(int).tolist()
    return [(b ^ p) for b, p in zip(bits, pn)]


def descramble(bits: list[int], seed: int = 2026) -> list[int]:
    """Descramble bits (identical operation to scramble — XOR is self-inverse).

    Args:
        bits: Scrambled bits.
        seed: Same seed used for scrambling.

    Returns:
        Original bits.
    """
    return scramble(bits, seed)


# Aliases for test discovery
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble
scramble_bits = scramble
descramble_bits = descramble
