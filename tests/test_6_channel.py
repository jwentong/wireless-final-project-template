import numpy as np
from src.channel import awgn_channel
from src.modulation import qpsk_modulate

# 生成测试符号
test_bits = np.random.randint(0, 2, 200, dtype=np.int8)
symbols = qpsk_modulate(test_bits)

# 测试1：固定种子可复现性
out1 = awgn_channel(symbols, 12, 2026)
out2 = awgn_channel(symbols, 12, 2026)
print(f"固定种子可复现性: {'✅ 通过' if np.allclose(out1, out2) else '❌ 失败'}")

# 测试2：高SNR噪声更小
out_low_snr = awgn_channel(symbols, 0, 2026)
out_high_snr = awgn_channel(symbols, 20, 2026)
noise_low = np.mean(np.abs(out_low_snr - symbols) ** 2)
noise_high = np.mean(np.abs(out_high_snr - symbols) ** 2)
print(f"SNR越高噪声越小: {'✅ 通过' if noise_low > noise_high else '❌ 失败'}")