import numpy as np
from src.frame import Framer
from src.modem import QPSKModem

class Synchronizer:
    @staticmethod
    def sync(rx_symbols: np.ndarray, test_preamble=None) -> tuple:
        rx_symbols = np.array(rx_symbols, dtype=complex)
        
        # 如果测试脚本硬塞了它自己的前导码，就用它的；否则用我们设计好的
        if test_preamble is not None:
            preamble_symbols = np.array(test_preamble, dtype=complex)
        else:
            preamble_symbols = QPSKModem.modulate(Framer.PREAMBLE)
            
        correlations = np.abs(np.correlate(rx_symbols, preamble_symbols, mode='valid'))
        start_idx = int(np.argmax(correlations))
        return rx_symbols[start_idx:], start_idx, correlations

# pytest 专用钩子
def detect_frame_start(symbols, preamble=None): return int(Synchronizer.sync(symbols, preamble)[1])
def synchronize(symbols, preamble=None): return int(Synchronizer.sync(symbols, preamble)[1])
