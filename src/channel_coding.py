"""(3,1) repetition code and optional convolutional code (Level 3)."""

from __future__ import annotations

from src.conv_coding import conv_encode, viterbi_decode

CODING_RATES = {"repeat": 1.0 / 3.0, "conv": 0.5}


def _repeat_encode(bits: list[int]) -> list[int]:
    encoded: list[int] = []
    for bit in bits:
        b = int(bit)
        encoded.extend([b, b, b])
    return encoded


def _repeat_decode(bits: list[int]) -> list[int]:
    decoded: list[int] = []
    for i in range(0, len(bits), 3):
        triplet = bits[i : i + 3]
        if len(triplet) < 3:
            triplet = triplet + [0] * (3 - len(triplet))
        decoded.append(1 if sum(int(x) for x in triplet) >= 2 else 0)
    return decoded


def channel_encode(bits: list[int], mode: str = "repeat") -> list[int]:
    data = [int(b) for b in bits]
    if mode == "conv":
        return conv_encode(data)
    if mode != "repeat":
        raise ValueError(f"Unknown FEC mode: {mode}")
    return _repeat_encode(data)


def channel_decode(bits: list[int], mode: str = "repeat") -> list[int]:
    data = [int(b) for b in bits]
    if mode == "conv":
        return viterbi_decode(data)
    if mode != "repeat":
        raise ValueError(f"Unknown FEC mode: {mode}")
    return _repeat_decode(data)
