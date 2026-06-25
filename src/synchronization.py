import numpy as np

def synchronize(received_symbols, preamble=None, threshold=0.5):
    received_symbols = np.array(received_symbols, dtype=complex)
    if preamble is not None:
        preamble = np.array(preamble, dtype=complex)
    else:
        from src.framing import PREAMBLE_BITS
        from src.modulation import qpsk_modulate
        preamble = np.array(qpsk_modulate(PREAMBLE_BITS), dtype=complex)
    corr = np.correlate(received_symbols, preamble, mode="valid")
    corr_abs = np.abs(corr)
    peak_idx = int(np.argmax(corr_abs))
    return peak_idx

def detect_frame_start(received_symbols, preamble=None):
    return synchronize(received_symbols, preamble)

def find_preamble(received_symbols, preamble=None):
    return synchronize(received_symbols, preamble)

def sync(received_symbols, preamble=None):
    return synchronize(received_symbols, preamble)

def compute_sync_metric(received_symbols, preamble):
    received_symbols = np.array(received_symbols, dtype=complex)
    preamble = np.array(preamble, dtype=complex)
    corr = np.correlate(received_symbols, preamble, mode="valid")
    return np.abs(corr)
