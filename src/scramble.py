import random


def _pn_sequence(length: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(0, 1) for _ in range(length)]


def scramble(bits: list[int], seed: int) -> list[int]:
    pn = _pn_sequence(len(bits), seed)
    return [b ^ p for b, p in zip(bits, pn)]


def descramble(bits: list[int], seed: int) -> list[int]:
    return scramble(bits, seed)


def no_scramble(bits: list[int], seed: int) -> list[int]:
    return list(bits)


def no_descramble(bits: list[int], seed: int) -> list[int]:
    return list(bits)


SCRAMBLE_SCHEMES = {
    "pn": (scramble, descramble),
    "none": (no_scramble, no_descramble),
}


def get_scramble(name: str):
    return SCRAMBLE_SCHEMES.get(name, (scramble, descramble))
