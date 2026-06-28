def repetition_encode(bits: list[int], repeat: int = 3) -> list[int]:
    if repeat <= 0 or repeat % 2 == 0:
        raise ValueError("repeat must be a positive odd integer")
    encoded: list[int] = []
    for bit in bits:
        encoded.extend([int(bit)] * repeat)
    return encoded


def repetition_decode(bits: list[int], repeat: int = 3) -> list[int]:
    if repeat <= 0 or repeat % 2 == 0:
        raise ValueError("repeat must be a positive odd integer")
    decoded: list[int] = []
    limit = len(bits) - (len(bits) % repeat)
    for i in range(0, limit, repeat):
        group = bits[i : i + repeat]
        decoded.append(1 if sum(group) >= (repeat // 2 + 1) else 0)
    return decoded


def channel_encode(bits: list[int]) -> list[int]:
    return repetition_encode(bits, 3)


def channel_decode(bits: list[int]) -> list[int]:
    return repetition_decode(bits, 3)


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
