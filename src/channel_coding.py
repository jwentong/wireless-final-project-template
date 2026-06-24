"""(3,1) repetition code with majority-vote decoding."""

from __future__ import annotations


def channel_encode(bits: list[int]) -> list[int]:
    encoded: list[int] = []
    for bit in bits:
        b = int(bit)
        encoded.extend([b, b, b])
    return encoded


def channel_decode(bits: list[int]) -> list[int]:
    decoded: list[int] = []
    for i in range(0, len(bits), 3):
        triplet = bits[i : i + 3]
        if len(triplet) < 3:
            triplet = triplet + [0] * (3 - len(triplet))
        decoded.append(1 if sum(int(x) for x in triplet) >= 2 else 0)
    return decoded
