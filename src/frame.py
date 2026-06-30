import numpy as np
from .framer import build_frame as _build_frame_original, parse_frame as _parse_frame_original, crc8, PREAMBLE_BITS


def build_frame(payload_bits, coded_payload_bits=None):
    """
    兼容公开测试：支持单参数调用
    - 只传1个参数：payload同时作为原始载荷和编码载荷
    - 传2个参数：按原设计区分原始载荷和编码后载荷
    """
    if coded_payload_bits is None:
        original = np.array(payload_bits, dtype=np.int8)
        coded = original.copy()
    else:
        original = np.array(payload_bits, dtype=np.int8)
        coded = np.array(coded_payload_bits, dtype=np.int8)
    return _build_frame_original(original, coded)


def parse_frame(frame_bits):
    """包装原解析函数，补充测试需要的字段名"""
    result = _parse_frame_original(frame_bits)
    # 统一转为 Python 列表，兼容 numpy 数组和原生列表两种输入
    coded_payload_list = list(result["coded_payload"])
    # 兼容测试的字段命名
    result["payload"] = coded_payload_list
    result["payload_bits"] = coded_payload_list
    result["length"] = result["payload_length"]
    return result