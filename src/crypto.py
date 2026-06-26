"""Scramble/descramble module using PN sequence (XOR with random bits).

Uses numpy's RNG with a fixed seed for reproducible pseudo-random sequence generation.
The same seed produces the same sequence, making XOR-based scrambling reversible.
"""

import numpy as np


def scramble(bits: list[int], seed: int = 2026) -> list[int]:
    """Scramble bitstream using XOR with a seeded pseudo-random sequence.

    Args:
        bits: Input bit list.
        seed: Random seed for reproducibility.

    Returns:
        Scrambled bit list (same length as input).
    """
    rng = np.random.default_rng(seed)
    pn_bits = rng.integers(0, 2, size=len(bits))
    return [int(b ^ int(p)) for b, p in zip(bits, pn_bits)]


def descramble(bits: list[int], seed: int = 2026) -> list[int]:
    """Descramble bitstream (XOR with same PN sequence, same seed).

    Since XOR is its own inverse, this is identical to scramble.

    Args:
        bits: Scrambled bit list.
        seed: Same seed used for scrambling.

    Returns:
        Original (descrambled) bit list.
    """
    return scramble(bits, seed)


# Alternative function names for test discovery
def scramble_bits(bits: list[int], seed: int = 2026) -> list[int]:
    """Alias for scramble."""
    return scramble(bits, seed)


def descramble_bits(bits: list[int], seed: int = 2026) -> list[int]:
    """Alias for descramble."""
    return descramble(bits, seed)


def encrypt(bits: list[int], seed: int = 2026) -> list[int]:
    """Alias for scramble."""
    return scramble(bits, seed)


def encrypt_bits(bits: list[int], seed: int = 2026) -> list[int]:
    """Alias for scramble."""
    return scramble(bits, seed)


def decrypt(bits: list[int], seed: int = 2026) -> list[int]:
    """Alias for descramble."""
    return descramble(bits, seed)


def decrypt_bits(bits: list[int], seed: int = 2026) -> list[int]:
    """Alias for descramble."""
    return descramble(bits, seed)
