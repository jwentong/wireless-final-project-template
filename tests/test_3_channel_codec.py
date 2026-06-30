import numpy as np
from src.channel_codec import hamming_encode, hamming_decode

# 测试1：无错编译码可逆性
test_bits = np.array([1,0,1,0, 0,1,1,0], dtype=np.int8)
coded = hamming_encode(test_bits)
decoded = hamming_decode(coded)
print(f"无错译码可逆性: {'✅ 通过' if np.array_equal(test_bits, decoded[:len(test_bits)]) else '❌ 失败'}")

# 测试2：单比特纠错能力
coded_with_error = coded.copy()
coded_with_error[3] ^= 1  # 翻转第 3 位
decoded_fixed = hamming_decode(coded_with_error)
print(f"单比特纠错能力: {'✅ 通过' if np.array_equal(test_bits, decoded_fixed[:len(test_bits)]) else '❌ 失败'}")