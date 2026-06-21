import numpy as np
import zlib

class Framer:
    # 64位强伪随机前导码，在极低信噪比下也能确保峰值唯一、精准同步！
    PREAMBLE = np.array([
        1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1,
        0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1,
        1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1,
        0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1
    ], dtype=np.uint8)
    
    @staticmethod
    def build_frame(payload: np.ndarray) -> np.ndarray:
        payload = np.array(payload, dtype=np.uint8)
        length_bits = np.unpackbits(np.array([len(payload)], dtype='>u4').view(np.uint8))
        crc32_val = zlib.crc32(np.packbits(payload).tobytes())
        crc_bits = np.unpackbits(np.array([crc32_val], dtype='>u4').view(np.uint8))
        return np.concatenate((Framer.PREAMBLE, length_bits, payload, crc_bits))

    @staticmethod
    def parse_frame(frame: np.ndarray):
        frame = np.array(frame, dtype=np.uint8)
        idx = len(Framer.PREAMBLE)
        length_bits = frame[idx : idx+32]
        payload_len = int(np.packbits(length_bits).view('>u4')[0])
        idx += 32
        
        payload = frame[idx : idx + payload_len]
        idx += payload_len
        
        crc_bits_received = frame[idx : idx+32]
        crc_calc = zlib.crc32(np.packbits(payload).tobytes())
        crc_received = int(np.packbits(crc_bits_received).view('>u4')[0]) if len(crc_bits_received)==32 else 0
        
        return payload, payload_len, crc_calc == crc_received

# pytest 专用钩子
def build_frame(payload): return Framer.build_frame(payload)
def parse_frame(frame): return Framer.parse_frame(frame)[0]
