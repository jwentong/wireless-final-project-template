import random


def pn_bits(length: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.getrandbits(1) for _ in range(length)]


def scramble_bits(bits: list[int], seed: int) -> list[int]:
    stream = pn_bits(len(bits), seed + 0x5A17)
    return [int(bit) ^ key for bit, key in zip(bits, stream)]


def descramble_bits(bits: list[int], seed: int) -> list[int]:
    return scramble_bits(bits, seed)
