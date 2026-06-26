import numpy as np


def synchronize(received_symbols, preamble):
    rx = np.asarray(received_symbols, dtype=complex)
    pre = np.asarray(preamble, dtype=complex)
    if len(rx) < len(pre) or len(pre) == 0:
        return {"start_index": 0, "correlation": []}
    corr = np.array(
        [abs(np.vdot(pre, rx[i : i + len(pre)])) for i in range(0, len(rx) - len(pre) + 1)]
    )
    return {"start_index": int(np.argmax(corr)), "correlation": corr.tolist()}


detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize

