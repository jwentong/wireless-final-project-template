from __future__ import annotations


def _clean_bits(bits) -> list[int]:
    return [1 if int(bit) else 0 for bit in list(bits)]


def channel_encode(bits, repeat: int = 3) -> list[int]:
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    encoded: list[int] = []
    for bit in _clean_bits(bits):
        encoded.extend([bit] * repeat)
    return encoded


def channel_decode(bits, repeat: int = 3, original_len: int | None = None) -> list[int]:
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    clean = _clean_bits(bits)
    decoded: list[int] = []
    for i in range(0, len(clean), repeat):
        group = clean[i : i + repeat]
        if not group:
            continue
        decoded.append(1 if sum(group) >= (len(group) / 2.0) else 0)
    if original_len is not None:
        decoded = decoded[: max(0, int(original_len))]
    return decoded


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode
