import numpy as np

# 13 位巴克码
_BARKER_13 = np.array([1,1,1,1,1,0,0,1,1,0,1,0,1], dtype=np.int8)
# 前导：巴克码重复 8 次，共 104 bit
PREAMBLE_BITS = np.tile(_BARKER_13, 8)
PREAMBLE_LEN = len(PREAMBLE_BITS)  # 104 bit

# CRC-8 多项式 0x07
_CRC8_POLY = 0x07


def crc8(bits: np.ndarray) -> np.ndarray:
    """计算 8 位 CRC 校验值，返回 8 bit 数组"""
    crc = 0
    for bit in bits:
        crc = (crc << 1) | int(bit)
        if crc & 0x100:
            crc ^= _CRC8_POLY
        crc &= 0xFF
    # 转为 8 位比特，高位在前
    crc_bits = []
    for i in range(7, -1, -1):
        crc_bits.append((crc >> i) & 1)
    return np.array(crc_bits, dtype=np.int8)


def build_frame(original_payload_bits: np.ndarray, coded_payload_bits: np.ndarray) -> np.ndarray:
    """
    构建完整帧
    :param original_payload_bits: 源编码后、扰码前的原始载荷比特（用于 length 和 CRC）
    :param coded_payload_bits: 信道编码后的载荷比特（作为帧数据部分）
    :return: 完整帧比特流
    """
    # 1. length 字段：32 位无符号整数，大端模式
    payload_len = len(original_payload_bits)
    length_bits = []
    for i in range(31, -1, -1):
        length_bits.append((payload_len >> i) & 1)
    length_bits = np.array(length_bits, dtype=np.int8)
    
    # 2. CRC 校验：覆盖原始载荷比特
    crc_bits = crc8(original_payload_bits)
    
    # 3. 拼接完整帧：前导 + length + 编码后载荷 + CRC
    frame = np.concatenate([PREAMBLE_BITS, length_bits, coded_payload_bits, crc_bits])
    return frame


def parse_frame(frame_bits: np.ndarray) -> dict:
    """
    解析完整帧
    :param frame_bits: 同步后截取的完整帧比特流
    :return: 字典，包含 payload_length、coded_payload、frame_crc
    """
    ptr = PREAMBLE_LEN
    
    # 解析 length 字段（32 bit）
    length_bits = frame_bits[ptr:ptr+32]
    payload_length = 0
    for bit in length_bits:
        payload_length = (payload_length << 1) | int(bit)
    ptr += 32
    
    # 解析 CRC（最后 8 bit）
    crc_start = len(frame_bits) - 8
    frame_crc_bits = frame_bits[crc_start:]
    frame_crc = 0
    for bit in frame_crc_bits:
        frame_crc = (frame_crc << 1) | int(bit)
    
    # 编码后载荷：length 之后，CRC 之前
    coded_payload = frame_bits[ptr:crc_start]
    
    return {
        "payload_length": payload_length,
        "coded_payload": coded_payload,
        "frame_crc": frame_crc
    }