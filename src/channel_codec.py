"""Repetition-3 channel coding."""

from __future__ import annotations


def repetition_encode(bits: list[int], repeat: int = 3) -> list[int]:
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    encoded: list[int] = []
    for bit in bits:
        encoded.extend([int(bit)] * repeat)
    return encoded


def repetition_decode(bits: list[int], repeat: int = 3) -> list[int]:
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    if len(bits) % repeat != 0:
        raise ValueError("encoded bit length must be divisible by repeat")

    decoded: list[int] = []
    threshold = repeat / 2
    for index in range(0, len(bits), repeat):
        group = [int(bit) for bit in bits[index : index + repeat]]
        decoded.append(1 if sum(group) > threshold else 0)
    return decoded


channel_encode = repetition_encode
channel_decode = repetition_decode
encode_bits = repetition_encode
decode_bits = repetition_decode
encode = repetition_encode
decode = repetition_decode
