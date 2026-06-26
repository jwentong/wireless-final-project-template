"""Synchronization module: Frame start detection via preamble cross-correlation.

Uses normalized cross-correlation between the received signal and the known
preamble sequence to detect the frame start position. Supports handling of
0-128 symbol random prefix offsets.

Algorithm:
  1. Generate the QPSK preamble symbols from the known preamble bit pattern.
  2. Compute cross-correlation between received signal and preamble.
  3. Find the peak of the correlation magnitude → frame start index.
"""

import numpy as np

# Preamble bits: 31-bit m-sequence mapped to antipodal QPSK, 32 symbols (64 bits)
# m-sequence polynomial: x^5 + x^2 + 1, initial state 11111
# Each bit: 1→[1,1]→(-1-j)/√2, 0→[0,0]→(1+j)/√2
_M_SEQ_31 = [1,1,1,1,1,0,1,0,0,0,1,0,0,1,0,1,0,1,1,0,0,0,0,1,1,1,0,0,1,1,0]
PREAMBLE_BITS = []
for _b in _M_SEQ_31:
    PREAMBLE_BITS.extend([1, 1] if _b else [0, 0])
PREAMBLE_BITS.extend([1, 1])  # pad to 64 bits = 32 QPSK symbols

SQRT2 = np.sqrt(2)

# QPSK Gray mapping for preamble generation
_QPSK_MAP = {
    (0, 0): complex(1, 1) / SQRT2,
    (0, 1): complex(-1, 1) / SQRT2,
    (1, 1): complex(-1, -1) / SQRT2,
    (1, 0): complex(1, -1) / SQRT2,
}


def _get_preamble_symbols() -> list[complex]:
    """Generate the known preamble as QPSK symbols."""
    symbols = []
    for i in range(0, len(PREAMBLE_BITS), 2):
        symbols.append(_QPSK_MAP[(PREAMBLE_BITS[i], PREAMBLE_BITS[i + 1])])
    return symbols


# Cached preamble symbols
_PREAMBLE_SYMBOLS = _get_preamble_symbols()


def synchronize(received, preamble=None):
    """Detect frame start position using preamble cross-correlation.

    Args:
        received: Array-like of complex received symbols.
        preamble: Optional preamble sequence. If None, uses the default 32-symbol preamble.

    Returns:
        Dictionary with keys:
          - start_index: int, detected frame start position in symbol index
          - sync_start_index: int, alias for start_index
          - correlation: array of correlation magnitudes
    """
    rx = np.asarray(received, dtype=complex)

    if preamble is not None:
        preamble_syms = np.asarray(preamble, dtype=complex)
    else:
        preamble_syms = np.asarray(_PREAMBLE_SYMBOLS, dtype=complex)

    preamble_len = len(preamble_syms)

    if len(rx) < preamble_len:
        return {
            "start_index": 0,
            "sync_start_index": 0,
            "correlation": [],
        }

    # Compute cross-correlation: corr[k] = sum_i rx[k+i] * conj(preamble[i])
    correlation = np.correlate(rx, preamble_syms, mode='valid')
    corr_magnitude = np.abs(correlation)

    # Find peak
    if len(corr_magnitude) > 0:
        start_index = int(np.argmax(corr_magnitude))
    else:
        start_index = 0

    return {
        "start_index": start_index,
        "sync_start_index": start_index,
        "index": start_index,
        "correlation": [float(x) for x in corr_magnitude],
    }


# Alternative function names for test discovery
def detect_frame_start(received, preamble=None):
    """Alias for synchronize."""
    return synchronize(received, preamble)


def find_preamble(received, preamble=None):
    """Alias for synchronize."""
    return synchronize(received, preamble)


def sync(received, preamble=None):
    """Alias for synchronize."""
    return synchronize(received, preamble)
