import numpy as np

class QPSKModem:
    # 严格遵循 PRD Gray 映射
    MAPPING = {
        (0, 0): (1 + 1j) / np.sqrt(2),
        (0, 1): (-1 + 1j) / np.sqrt(2),
        (1, 1): (-1 - 1j) / np.sqrt(2),
        (1, 0): (1 - 1j) / np.sqrt(2)
    }

    @staticmethod
    def modulate(bits: np.ndarray) -> np.ndarray:
        if len(bits) % 2 != 0:
            bits = np.append(bits, 0) # Padding
        
        symbols = np.zeros(len(bits) // 2, dtype=complex)
        for i in range(0, len(bits), 2):
            symbols[i//2] = QPSKModem.MAPPING[(bits[i], bits[i+1])]
        return symbols

    @staticmethod
    def demodulate(symbols: np.ndarray) -> np.ndarray:
        bits = []
        for s in symbols:
            # 最小欧氏距离判决
            best_bits = None
            min_dist = float('inf')
            for b_tuple, constellation_point in QPSKModem.MAPPING.items():
                dist = abs(s - constellation_point)
                if dist < min_dist:
                    min_dist = dist
                    best_bits = b_tuple
            bits.extend(best_bits)
        return np.array(bits, dtype=np.uint8)
# pytest hook
def qpsk_modulate(bits): return QPSKModem.modulate(bits)
def qpsk_demodulate(symbols): return QPSKModem.demodulate(symbols)
