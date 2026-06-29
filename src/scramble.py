"""Scrambling: XOR payload bits with an LFSR-generated PN sequence.

Uses a 15-bit Fibonacci LFSR (primitive polynomial x^15 + x^14 + 1). The seed
initializes the register state, so the key stream is deterministic and
reproducible. XOR is self-inverse, hence ``descramble`` is identical to
``scramble`` with the same seed. Scrambling breaks long runs of 0/1, which helps
synchronization and keeps the modulated signal power balanced.
"""
from __future__ import annotations

_LFSR_BITS = 15
_MASK = (1 << _LFSR_BITS) - 1  # 0x7FFF


def _pn_sequence(n: int, seed: int) -> list[int]:
    """Generate ``n`` PN bits from a 15-bit LFSR seeded by ``seed`` (forced nonzero)."""
    state = (seed & _MASK) or 0x1
    out: list[int] = []
    for _ in range(n):
        out.append(state & 1)
        fb = ((state >> 14) ^ (state >> 13)) & 1  # taps at bit 15 and 14
        state = ((state >> 1) | (fb << (_LFSR_BITS - 1))) & _MASK
    return out


def scramble(bits: list[int], seed: int = 2026) -> list[int]:
    """XOR ``bits`` with PN(``seed``). Reversible by re-applying with same seed."""
    return [int(b) ^ p for b, p in zip(bits, _pn_sequence(len(bits), seed))]


def descramble(bits: list[int], seed: int = 2026) -> list[int]:
    """Inverse of :func:`scramble` (identical operation; XOR is self-inverse)."""
    return scramble(bits, seed)
