"""PN sequence XOR scrambling."""

from __future__ import annotations

# Primitive polynomial x^16 + x^14 + x^13 + x^11 + 1
TAPS = (16, 14, 13, 11)


def _lfsr_bits(length: int, seed: int) -> list[int]:
    state = (int(seed) & 0xFFFF) or 0xACE1
    out: list[int] = []
    for _ in range(length):
        out.append(state & 1)
        feedback = 0
        for tap in TAPS:
            feedback ^= (state >> (16 - tap)) & 1
        state = ((state << 1) & 0xFFFF) | feedback
    return out


def scramble(bits: list[int], seed: int = 2026) -> list[int]:
    pn = _lfsr_bits(len(bits), seed)
    return [int(b) ^ int(p) for b, p in zip(bits, pn)]


def descramble(bits: list[int], seed: int = 2026) -> list[int]:
    return scramble(bits, seed)
