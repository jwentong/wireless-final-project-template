import numpy as np
from src.framing import PREAMBLE_BITS
from src.modulation import qpsk_modulate, bpsk_modulate, qam16_modulate

_PREAMBLE_QPSK = np.array(qpsk_modulate(PREAMBLE_BITS), dtype=complex)
_PREAMBLE_BPSK = np.array(bpsk_modulate(PREAMBLE_BITS), dtype=complex)
_PREAMBLE_QAM16 = np.array(qam16_modulate(PREAMBLE_BITS), dtype=complex)

_PREAMBLE_MAP = {
    "qpsk": _PREAMBLE_QPSK,
    "bpsk": _PREAMBLE_BPSK,
    "16qam": _PREAMBLE_QAM16,
}


def detect_frame_start(symbols, preamble=None, modulation="qpsk"):
    sym_arr = np.array(symbols, dtype=complex)
    if preamble is not None:
        templ = np.array(preamble, dtype=complex)
    else:
        templ = _PREAMBLE_MAP.get(modulation, _PREAMBLE_QPSK)
    if len(sym_arr) < len(templ):
        return 0
    corr = np.correlate(sym_arr, templ, mode="valid")
    return int(np.argmax(np.abs(corr)))


synchronize = detect_frame_start
find_preamble = detect_frame_start
