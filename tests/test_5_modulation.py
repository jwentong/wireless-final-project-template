import numpy as np
from src.modulation import qpsk_modulate, qpsk_demodulate

# 测试1：无噪下调制解调可逆性
test_bits = np.array([1,0,1,1, 0,0,1,0, 1,1,0,1], dtype=np.int8)
symbols = qpsk_modulate(test_bits)
demod_bits = qpsk_demodulate(symbols)
print(f"无噪解调可逆性: {'✅ 通过' if np.array_equal(test_bits, demod_bits[:len(test_bits)]) else '❌ 失败'}")

# 测试2：符号平均功率验证
avg_power = np.mean(np.abs(symbols) ** 2)
print(f"符号平均功率: {avg_power:.4f}，归一化验证: {'✅ 通过' if abs(avg_power - 1.0) < 1e-6 else '❌ 失败'}")

# 测试3：奇数长度补零测试
odd_bits = np.array([1,0,1], dtype=np.int8)
sym_odd = qpsk_modulate(odd_bits)
demod_odd = qpsk_demodulate(sym_odd)
print(f"奇数长度补零解调: {'✅ 通过' if np.array_equal(odd_bits, demod_odd[:len(odd_bits)]) else '❌ 失败'}")