from __future__ import annotations


REPETITION = 3


def channel_encode(bits: list[int]) -> list[int]:
    coded: list[int] = []
    for bit in bits:
        coded.extend([int(bit)] * REPETITION)
    return coded


def channel_decode(bits: list[int]) -> list[int]:
    decoded: list[int] = []
    usable = len(bits) - (len(bits) % REPETITION)
    for offset in range(0, usable, REPETITION):
        group = [int(x) for x in bits[offset : offset + REPETITION]]
        decoded.append(1 if sum(group) >= 2 else 0)
    return decoded


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode

