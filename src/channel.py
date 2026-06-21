import numpy as np

class AWGNChannel:
    @staticmethod
    def pass_channel(symbols: np.ndarray, snr_db: float, seed: int) -> np.ndarray:
        np.random.seed(seed)
        
        # 1. 添加随机前置偏移 (0~128个符号)
        offset = np.random.randint(0, 129)
        padding_symbols = (np.random.randn(offset) + 1j*np.random.randn(offset)) / np.sqrt(2)
        symbols_with_offset = np.concatenate((padding_symbols, symbols))
        
        # 2. 加入 AWGN 噪声
        # 符号平均功率为 1
        snr_linear = 10 ** (snr_db / 10.0)
        noise_variance = 1.0 / snr_linear
        noise = np.sqrt(noise_variance / 2) * (np.random.randn(len(symbols_with_offset)) + 1j * np.random.randn(len(symbols_with_offset)))
        
        return symbols_with_offset + noise, offset
# pytest hook
def awgn_channel(symbols, snr_db=12, seed=2026): return AWGNChannel.pass_channel(symbols, snr_db, seed)[0]
