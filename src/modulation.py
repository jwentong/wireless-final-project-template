"""QPSK modulation / demodulation with Gray coding.

Constellation mapping (Gray code):
    00 ->  (+1 + 1j) / sqrt(2)   (Quadrant I)
    01 ->  (-1 + 1j) / sqrt(2)   (Quadrant II)
    11 ->  (-1 - 1j) / sqrt(2)   (Quadrant III)
    10 ->  (+1 - 1j) / sqrt(2)   (Quadrant IV)

Average symbol power = 1.
"""

import numpy as np

# Normalization factor for unit power
_NORM = 1.0 / np.sqrt(2)

# Gray-coded constellation lookup: (b1, b0) -> complex symbol
# b1 = first bit of pair, b0 = second bit of pair
_CONSTELLATION = {
    (0, 0): complex(_NORM, _NORM),    # Quadrant I
    (0, 1): complex(-_NORM, _NORM),   # Quadrant II
    (1, 1): complex(-_NORM, -_NORM),  # Quadrant III
    (1, 0): complex(_NORM, -_NORM),   # Quadrant IV
}


def qpsk_modulate(bits: list[int]) -> np.ndarray:
    """Modulate bits into QPSK complex symbols.

    Each pair of bits (b1, b0) maps to one QPSK symbol.
    If the number of bits is odd, a trailing 0 is appended for padding.

    Args:
        bits: List of 0/1 ints.

    Returns:
        Complex-valued numpy array of QPSK symbols.
    """
    b = list(bits)
    if len(b) % 2 != 0:
        b.append(0)  # padding for odd-length bitstream

    symbols = []
    for i in range(0, len(b), 2):
        key = (int(b[i]), int(b[i + 1]))
        symbols.append(_CONSTELLATION[key])

    return np.array(symbols, dtype=complex)


def qpsk_demodulate(symbols: np.ndarray) -> list[int]:
    """Demodulate QPSK symbols back to bits (hard decision).

    Decision rule: sign of real part -> b1, sign of imag part -> b0.

    Args:
        symbols: Complex-valued numpy array.

    Returns:
        List of demodulated bits.
    """
    bits = []
    for s in np.asarray(symbols).flat:
        real = s.real
        imag = s.imag
        if real >= 0:
            if imag >= 0:
                bits.extend([0, 0])  # Quadrant I
            else:
                bits.extend([1, 0])  # Quadrant IV
        else:
            if imag >= 0:
                bits.extend([0, 1])  # Quadrant II
            else:
                bits.extend([1, 1])  # Quadrant III
    return bits


# Aliases for test discovery
modulate = qpsk_modulate
demodulate = qpsk_demodulate
qpsk_mapper = qpsk_modulate
qpsk_demapper = qpsk_demodulate
modulate_qpsk = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
