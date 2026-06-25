import numpy as np


def synchronize(received, preamble=None):
    """Find frame start by matched correlation with a known QPSK preamble."""
    rx = np.asarray(received, dtype=complex)
    if preamble is None:
        from .framing import PREAMBLE_BITS
        from .modulation import qpsk_modulate

        preamble = qpsk_modulate(PREAMBLE_BITS)
    pre = np.asarray(preamble, dtype=complex)
    if rx.size < pre.size or pre.size == 0:
        return {"start_index": 0, "sync_start_index": 0, "peak": 0.0, "correlation": []}
    corr = np.abs(np.correlate(rx, pre, mode="valid"))
    start = int(np.argmax(corr))
    peak = float(corr[start])
    return {
        "start_index": start,
        "sync_start_index": start,
        "index": start,
        "peak": peak,
        "correlation": corr.tolist(),
    }


detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize
