import numpy as np


_INV_SQRT2 = 1.0 / np.sqrt(2.0)
_MAP = {
    (0, 0): (1 + 1j) * _INV_SQRT2,
    (0, 1): (-1 + 1j) * _INV_SQRT2,
    (1, 1): (-1 - 1j) * _INV_SQRT2,
    (1, 0): (1 - 1j) * _INV_SQRT2,
}


def qpsk_modulate(bits):
    bit_list = [int(bit) for bit in bits]
    if len(bit_list) % 2:
        bit_list.append(0)
    symbols = [_MAP[(bit_list[i], bit_list[i + 1])] for i in range(0, len(bit_list), 2)]
    return np.array(symbols, dtype=complex)


def qpsk_demodulate(symbols):
    out = []
    for sym in np.asarray(symbols, dtype=complex):
        if sym.real >= 0 and sym.imag >= 0:
            out.extend([0, 0])
        elif sym.real < 0 and sym.imag >= 0:
            out.extend([0, 1])
        elif sym.real < 0 and sym.imag < 0:
            out.extend([1, 1])
        else:
            out.extend([1, 0])
    return out


modulate_qpsk = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_mapper = qpsk_modulate
qpsk_demapper = qpsk_demodulate
modulate = qpsk_modulate
demodulate = qpsk_demodulate

