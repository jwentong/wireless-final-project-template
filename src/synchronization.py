from __future__ import annotations

import numpy as np


def detect_frame_start(received_symbols, preamble) -> dict[str, object]:
    received = np.asarray(received_symbols, dtype=complex)
    reference = np.asarray(preamble, dtype=complex)
    if reference.size == 0 or received.size < reference.size:
        return {"start_index": 0, "correlation": np.array([], dtype=float), "peak_value": 0.0}
    corr = np.array(
        [abs(np.vdot(reference, received[i : i + reference.size])) for i in range(received.size - reference.size + 1)],
        dtype=float,
    )
    index = int(np.argmax(corr))
    return {"start_index": index, "correlation": corr, "peak_value": float(corr[index])}


synchronize = detect_frame_start
find_preamble = detect_frame_start
sync = detect_frame_start

