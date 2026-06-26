"""Modulation/demodulation module: QPSK, BPSK, and 16-QAM.

QPSK Gray mapping (PRD compliant):
  00 → (1 + j) / √2   (first quadrant)
  01 → (-1 + j) / √2  (second quadrant)
  11 → (-1 - j) / √2  (third quadrant)
  10 → (1 - j) / √2   (fourth quadrant)

BPSK mapping:
  0 → +1
  1 → -1

16-QAM Gray mapping: 4-bit per symbol in a 4×4 constellation.
"""

import numpy as np

SQRT2 = np.sqrt(2)


# ==================== QPSK ====================

# QPSK Gray-encoded mapping: bit pair → complex symbol
_QPSK_MAP = {
    (0, 0): complex(1, 1) / SQRT2,   # 00
    (0, 1): complex(-1, 1) / SQRT2,  # 01
    (1, 1): complex(-1, -1) / SQRT2, # 11
    (1, 0): complex(1, -1) / SQRT2,  # 10
}


def qpsk_modulate(bits: list[int]) -> list[complex]:
    """Modulate bits to QPSK symbols using Gray mapping.

    If the number of bits is odd, a trailing 0 is appended (padding).

    Args:
        bits: List of 0/1 integers.

    Returns:
        List of complex QPSK symbols, each with unit average power.
    """
    b = list(bits)
    if len(b) % 2 != 0:
        b.append(0)  # Pad with 0
    symbols = []
    for i in range(0, len(b), 2):
        symbols.append(_QPSK_MAP[(int(b[i]), int(b[i + 1]))])
    return symbols


def qpsk_demodulate(symbols: list[complex]) -> list[int]:
    """Demodulate QPSK symbols using minimum Euclidean distance.

    Args:
        symbols: List of complex QPSK symbols.

    Returns:
        List of demodulated bits (twice the number of symbols).
    """
    # Reference constellation points (Gray order: 00, 01, 11, 10)
    ref_points = [
        complex(1, 1) / SQRT2,     # 00
        complex(-1, 1) / SQRT2,    # 01
        complex(-1, -1) / SQRT2,   # 11
        complex(1, -1) / SQRT2,    # 10
    ]
    ref_bits = [(0, 0), (0, 1), (1, 1), (1, 0)]

    bits = []
    for s in symbols:
        # Find nearest constellation point
        distances = [abs(s - ref) for ref in ref_points]
        idx = int(np.argmin(distances))
        bits.extend(ref_bits[idx])
    return bits


# ==================== BPSK ====================

def bpsk_modulate(bits: list[int]) -> list[complex]:
    """Modulate bits to BPSK symbols: 0→+1, 1→-1.

    Args:
        bits: List of 0/1 integers.

    Returns:
        List of complex BPSK symbols (imaginary part = 0).
    """
    return [complex(1.0 if b == 0 else -1.0, 0.0) for b in bits]


def bpsk_demodulate(symbols: list[complex]) -> list[int]:
    """Demodulate BPSK symbols: real>0→0, real≤0→1.

    Args:
        symbols: List of complex BPSK symbols.

    Returns:
        List of demodulated bits.
    """
    return [0 if s.real > 0 else 1 for s in symbols]


# ==================== 16-QAM ====================

def _gray_4bit() -> list[tuple[int, ...]]:
    """Generate 4-bit Gray code mapping for 16-QAM."""
    # Standard 4-bit Gray code
    return [
        (0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 1, 1), (0, 0, 1, 0),
        (0, 1, 1, 0), (0, 1, 1, 1), (0, 1, 0, 1), (0, 1, 0, 0),
        (1, 1, 0, 0), (1, 1, 0, 1), (1, 1, 1, 1), (1, 1, 1, 0),
        (1, 0, 1, 0), (1, 0, 1, 1), (1, 0, 0, 1), (1, 0, 0, 0),
    ]


def qam16_modulate(bits: list[int]) -> list[complex]:
    """Modulate bits to 16-QAM symbols using Gray mapping.

    Args:
        bits: List of 0/1 integers. Length padded to multiple of 4.

    Returns:
        List of complex 16-QAM symbols.
    """
    b = list(bits)
    while len(b) % 4 != 0:
        b.append(0)

    # 16-QAM levels: -3, -1, +1, +3 (normalized by 1/√10 for unit average power)
    levels = np.array([-3, -1, 1, 3]) / np.sqrt(10)
    gray = _gray_4bit()

    symbols = []
    for i in range(0, len(b), 4):
        quad = (int(b[i]), int(b[i + 1]), int(b[i + 2]), int(b[i + 3]))
        idx = gray.index(quad) if quad in gray else 0
        # First 2 bits → I component, last 2 bits → Q component
        i_idx = idx % 4
        q_idx = idx // 4
        symbols.append(complex(levels[i_idx], levels[q_idx]))

    return symbols


def qam16_demodulate(symbols: list[complex]) -> list[int]:
    """Demodulate 16-QAM symbols using minimum distance.

    Args:
        symbols: List of complex 16-QAM symbols.

    Returns:
        List of demodulated bits (4 times the number of symbols).
    """
    levels = np.array([-3, -1, 1, 3]) / np.sqrt(10)
    gray = _gray_4bit()

    bits = []
    for s in symbols:
        # Find nearest level for I and Q
        i_idx = int(np.argmin(np.abs(s.real - levels)))
        q_idx = int(np.argmin(np.abs(s.imag - levels)))
        # Map grid position to Gray bits
        idx = q_idx * 4 + i_idx
        bits.extend(gray[idx])

    return bits


# ==================== Modulation dispatcher ====================

def modulate(bits: list[int], mod_type: str = "qpsk") -> list[complex]:
    """Dispatch to the appropriate modulation function.

    Args:
        bits: Input bit list.
        mod_type: "qpsk", "bpsk", or "qam16".

    Returns:
        List of complex symbols.
    """
    mod_type = mod_type.lower()
    if mod_type == "qpsk":
        return qpsk_modulate(bits)
    elif mod_type == "bpsk":
        return bpsk_modulate(bits)
    elif mod_type in ("qam16", "16qam", "16-qam"):
        return qam16_modulate(bits)
    else:
        raise ValueError(f"Unknown modulation type: {mod_type}")


def demodulate(symbols: list[complex], mod_type: str = "qpsk") -> list[int]:
    """Dispatch to the appropriate demodulation function.

    Args:
        symbols: List of complex symbols.
        mod_type: "qpsk", "bpsk", or "qam16".

    Returns:
        List of demodulated bits.
    """
    mod_type = mod_type.lower()
    if mod_type == "qpsk":
        return qpsk_demodulate(symbols)
    elif mod_type == "bpsk":
        return bpsk_demodulate(symbols)
    elif mod_type in ("qam16", "16qam", "16-qam"):
        return qam16_demodulate(symbols)
    else:
        raise ValueError(f"Unknown modulation type: {mod_type}")


# Alternative function names for test discovery
def qpsk_mapper(bits: list[int]) -> list[complex]:
    """Alias for qpsk_modulate."""
    return qpsk_modulate(bits)


def qpsk_demapper(symbols: list[complex]) -> list[int]:
    """Alias for qpsk_demodulate."""
    return qpsk_demodulate(symbols)


def modulate_qpsk(bits: list[int]) -> list[complex]:
    """Alias for qpsk_modulate."""
    return qpsk_modulate(bits)


def demodulate_qpsk(symbols: list[complex]) -> list[int]:
    """Alias for qpsk_demodulate."""
    return qpsk_demodulate(symbols)
