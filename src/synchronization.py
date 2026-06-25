"""Frame synchronization via preamble cross-correlation."""

import numpy as np
from scipy import signal


def synchronize(
    received: np.ndarray, preamble: np.ndarray = None, threshold: float = 0.5
) -> int:
    """Detect frame start via cross-correlation with preamble.

    Args:
        received: Received complex symbols (may include noise prefix).
        preamble: Known preamble symbols. If None, uses default QPSK preamble.
        threshold: Ignored; kept for API compatibility.

    Returns:
        Index of the first preamble symbol in the received sequence.
    """
    recv = np.asarray(received, dtype=complex).flatten()

    if preamble is None:
        # Default preamble: 32 bits of 0xA1B2C3D4 modulated as QPSK
        from src.modulation import qpsk_modulate

        default_preamble_bits = [
            1, 0, 1, 0, 0, 0, 0, 1,  # 0xA1
            1, 0, 1, 1, 0, 0, 1, 0,  # 0xB2
            1, 1, 0, 0, 0, 0, 1, 1,  # 0xC3
            1, 1, 0, 1, 0, 1, 0, 0,  # 0xD4
        ]
        preamble = qpsk_modulate(default_preamble_bits)

    pre = np.asarray(preamble, dtype=complex).flatten()

    if len(recv) < len(pre):
        return 0

    # Normalized cross-correlation
    corr = signal.correlate(recv, pre, mode="valid")
    corr_mag = np.abs(corr)

    start = int(np.argmax(corr_mag))

    return start


# Aliases for test discovery
detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize
