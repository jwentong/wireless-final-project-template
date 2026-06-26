"""Simple repetition channel code with majority decoding."""

from __future__ import annotations

from typing import Iterable, List


DEFAULT_REPETITIONS = 3


def _as_bits(bits: Iterable[int]) -> List[int]:
    return [1 if int(bit) else 0 for bit in bits]


def channel_encode(bits: Iterable[int], repetitions: int = DEFAULT_REPETITIONS) -> List[int]:
    """Encode each bit by repeating it an odd number of times."""
    reps = int(repetitions)
    if reps <= 0 or reps % 2 == 0:
        raise ValueError("repetitions must be a positive odd integer")
    encoded: List[int] = []
    for bit in _as_bits(bits):
        encoded.extend([bit] * reps)
    return encoded


def channel_decode(bits: Iterable[int], repetitions: int = DEFAULT_REPETITIONS) -> List[int]:
    """Decode a repetition code using majority decisions."""
    reps = int(repetitions)
    if reps <= 0 or reps % 2 == 0:
        raise ValueError("repetitions must be a positive odd integer")
    bit_list = _as_bits(bits)
    decoded: List[int] = []
    for i in range(0, len(bit_list), reps):
        group = bit_list[i : i + reps]
        if not group:
            continue
        decoded.append(1 if sum(group) >= (len(group) / 2.0) else 0)
    return decoded


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode

