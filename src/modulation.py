import numpy as np


SQRT2 = np.sqrt(2.0)
MAPPING = {
    (0, 0): (1 + 1j) / SQRT2,
    (0, 1): (-1 + 1j) / SQRT2,
    (1, 1): (-1 - 1j) / SQRT2,
    (1, 0): (1 - 1j) / SQRT2,
}


def qpsk_modulate(bits):
    clean = [int(b) & 1 for b in bits]
    if len(clean) % 2:
        clean.append(0)
    symbols = [MAPPING[(clean[i], clean[i + 1])] for i in range(0, len(clean), 2)]
    return np.asarray(symbols, dtype=complex)


def qpsk_demodulate(symbols):
    out = []
    for symbol in np.asarray(symbols, dtype=complex):
        if symbol.real >= 0 and symbol.imag >= 0:
            out.extend([0, 0])
        elif symbol.real < 0 and symbol.imag >= 0:
            out.extend([0, 1])
        elif symbol.real < 0 and symbol.imag < 0:
            out.extend([1, 1])
        else:
            out.extend([1, 0])
    return out


modulate_qpsk = qpsk_modulate
qpsk_mapper = qpsk_modulate
modulate = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_demapper = qpsk_demodulate
demodulate = qpsk_demodulate

