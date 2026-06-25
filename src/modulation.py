import numpy as np


QPSK_MAP = {
    (0, 0): (1 + 1j) / np.sqrt(2),
    (0, 1): (-1 + 1j) / np.sqrt(2),
    (1, 1): (-1 - 1j) / np.sqrt(2),
    (1, 0): (1 - 1j) / np.sqrt(2),
}

QPSK_DEMAP = {
    (True, True): (0, 0),
    (False, True): (0, 1),
    (False, False): (1, 1),
    (True, False): (1, 0),
}


def qpsk_modulate(bits: list[int]) -> list[complex]:
    if len(bits) % 2 != 0:
        bits = bits + [0]
    symbols = []
    for i in range(0, len(bits), 2):
        symbols.append(QPSK_MAP[(bits[i], bits[i + 1])])
    return symbols


def qpsk_demodulate(symbols: list[complex]) -> list[int]:
    bits = []
    for s in symbols:
        re_real = s.real > 0
        im_real = s.imag > 0
        b0, b1 = QPSK_DEMAP[(re_real, im_real)]
        bits.append(b0)
        bits.append(b1)
    return bits


BPSK_MAP = {0: 1 + 0j, 1: -1 + 0j}


def bpsk_modulate(bits: list[int]) -> list[complex]:
    return [BPSK_MAP[b] for b in bits]


def bpsk_demodulate(symbols: list[complex]) -> list[int]:
    return [0 if s.real > 0 else 1 for s in symbols]


QAM16_SCALE = 1 / np.sqrt(10)

QAM16_I_MAP = {
    (0, 0): -3,
    (0, 1): -1,
    (1, 1): 1,
    (1, 0): 3,
}

QAM16_DEMAP_I = {-3: (0, 0), -1: (0, 1), 1: (1, 1), 3: (1, 0)}


def qam16_modulate(bits: list[int]) -> list[complex]:
    if len(bits) % 4 != 0:
        bits = bits + [0] * (4 - len(bits) % 4)
    symbols = []
    for i in range(0, len(bits), 4):
        b0, b1, b2, b3 = bits[i], bits[i + 1], bits[i + 2], bits[i + 3]
        i_val = QAM16_I_MAP[(b0, b1)]
        q_val = QAM16_I_MAP[(b2, b3)]
        symbols.append(complex(i_val, q_val) * QAM16_SCALE)
    return symbols


def qam16_demodulate(symbols: list[complex]) -> list[int]:
    bits = []
    for s in symbols:
        i_unnorm = round(s.real / QAM16_SCALE)
        q_unnorm = round(s.imag / QAM16_SCALE)
        i_clamped = max(-3, min(3, i_unnorm))
        q_clamped = max(-3, min(3, q_unnorm))
        if i_clamped % 2 == 0:
            i_clamped += (-1 if i_clamped < 0 else 1)
        if q_clamped % 2 == 0:
            q_clamped += (-1 if q_clamped < 0 else 1)
        b0, b1 = QAM16_DEMAP_I[i_clamped]
        b2, b3 = QAM16_DEMAP_I[q_clamped]
        bits.extend([b0, b1, b2, b3])
    return bits
