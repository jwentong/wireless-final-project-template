from .frame import find_frame_start


def synchronize(received_symbols, preamble=None):
    symbols = [complex(x) for x in received_symbols]
    if preamble is None:
        start, peaks = find_frame_start(symbols)
        return {"start_index": start, "sync_start_index": start, "correlation": peaks}

    ref = [complex(x) for x in preamble]
    needed = len(ref)
    best_index = 0
    best_score = -1.0
    ref_energy = sum(abs(x) ** 2 for x in ref) or 1.0
    peaks = []
    for i in range(0, len(symbols) - needed + 1):
        window = symbols[i : i + needed]
        window_energy = sum(abs(x) ** 2 for x in window) or 1.0
        corr = sum(window[j] * ref[j].conjugate() for j in range(needed))
        score = abs(corr) / ((window_energy * ref_energy) ** 0.5)
        peaks.append(score)
        if score > best_score:
            best_score = score
            best_index = i
    return {"start_index": best_index, "sync_start_index": best_index, "correlation": peaks}


detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize
