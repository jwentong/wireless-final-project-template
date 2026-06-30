import numpy as np
from src.synchronization import find_frame_start
from src.framer import build_frame, PREAMBLE_BITS
from src.modulation import qpsk_modulate

# 构造测试数据：随机偏移 + 完整帧符号
np.random.seed(2026)
original_bits = np.random.randint(0, 2, 100, dtype=np.int8)
coded_bits = np.random.randint(0, 2, 175, dtype=np.int8)
frame_bits = build_frame(original_bits, coded_bits)
frame_symbols = qpsk_modulate(frame_bits)

# 添加 50 个符号的随机前置偏移
offset = 50
offset_symbols = np.random.randn(offset) + 1j * np.random.randn(offset)
full_signal = np.concatenate([offset_symbols, frame_symbols])

# 同步检测
detected_start = find_frame_start(full_signal)
error = abs(detected_start - offset)
print(f"真实前导起始位置: {offset}")
print(f"检测到的起始位置: {detected_start}")
print(f"同步误差: {error} 个符号")
print(f"同步精度验证: {'✅ 通过' if error <= 1 else '❌ 失败'}")