import numpy as np
from src.framer import PREAMBLE_BITS
from src.modulation import qpsk_modulate

# 本地前导符号（与main.py导入名保持一致）
LOCAL_PREAMBLE_SYMBOLS = qpsk_modulate(PREAMBLE_BITS)


def find_frame_start(received_symbols, preamble=None):
    """
    互相关法检测帧起始位置
    :param received_symbols: 接收端符号序列
    :param preamble: 可选，自定义前导符号；不传则使用默认本地前导
    :return: 帧起始符号索引（前导第一个符号位置）
    """
    if preamble is None:
        local_preamble = LOCAL_PREAMBLE_SYMBOLS
    else:
        local_preamble = np.array(preamble, dtype=np.complex128)
    
    corr = np.correlate(received_symbols, local_preamble, mode='valid')
    peak_idx = np.argmax(np.abs(corr))
    return int(peak_idx)


# 兼容公开测试接口别名
detect_frame_start = find_frame_start