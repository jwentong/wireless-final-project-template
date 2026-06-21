import numpy as np

class SourceCodec:
    @staticmethod
    def encode(text: str) -> np.ndarray:
        # 将字符串转为 UTF-8 字节，再转为 0/1 比特数组
        byte_array = text.encode('utf-8')
        bits = np.unpackbits(np.frombuffer(byte_array, dtype=np.uint8))
        return bits

    @staticmethod
    def decode(bits: np.ndarray) -> str:
        # 截断为8的整数倍
        valid_len = (len(bits) // 8) * 8
        bits = bits[:valid_len]
        byte_array = np.packbits(bits).tobytes()
        return byte_array.decode('utf-8', errors='replace')
# pytest hook
def source_encode(text): return SourceCodec.encode(text)
def source_decode(bits): return SourceCodec.decode(bits)
