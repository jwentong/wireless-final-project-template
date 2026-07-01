import numpy as np
from src.scrambler import scramble, descramble

# 生成随机测试比特
np.random.seed(2026)
test_bits = np.random.randint(0, 2, 200, dtype=np.int8)

scrambled = scramble(test_bits)
restored = descramble(scrambled)

print(f"原始比特前10位: {test_bits[:10]}")
print(f"加扰后前10位: {scrambled[:10]}")
print(f"可逆性验证: {'✅ 通过' if np.array_equal(test_bits, restored) else '❌ 失败'}")