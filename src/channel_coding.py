import numpy as np

class ChannelCodec:
    # 使用简单的 3 倍重复码
    @staticmethod
    def encode(bits: np.ndarray) -> np.ndarray:
        return np.repeat(bits, 3)

    @staticmethod
    def decode(bits: np.ndarray) -> np.ndarray:
        # 大多数投票表决法
        reshaped = bits[:(len(bits)//3)*3].reshape(-1, 3)
        sums = np.sum(reshaped, axis=1)
        return (sums >= 2).astype(np.uint8)
# pytest hook
def channel_encode(bits): return ChannelCodec.encode(np.array(bits))
def channel_decode(bits): return ChannelCodec.decode(np.array(bits))
