from math import sqrt


QPSK_SCALE = 1.0 / sqrt(2.0)
QPSK_MAPPING = {
    (0, 0): complex(QPSK_SCALE, QPSK_SCALE),
    (0, 1): complex(-QPSK_SCALE, QPSK_SCALE),
    (1, 1): complex(-QPSK_SCALE, -QPSK_SCALE),
    (1, 0): complex(QPSK_SCALE, -QPSK_SCALE),
}


def qpsk_modulate(bits: list[int]) -> list[complex]:
    padded = list(bits)
    if len(padded) % 2:
        padded.append(0)
    symbols = [QPSK_MAPPING[(padded[i], padded[i + 1])] for i in range(0, len(padded), 2)]
    return symbols


def qpsk_demodulate(symbols: list[complex]) -> list[int]:
    bits: list[int] = []
    for symbol in symbols:
        if symbol.real >= 0 and symbol.imag >= 0:
            bits.extend([0, 0])
        elif symbol.real < 0 and symbol.imag >= 0:
            bits.extend([0, 1])
        elif symbol.real < 0 and symbol.imag < 0:
            bits.extend([1, 1])
        else:
            bits.extend([1, 0])
    return bits


modulate = qpsk_modulate
demodulate = qpsk_demodulate
