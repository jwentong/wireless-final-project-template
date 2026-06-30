import numpy as np
from src.framer import build_frame, parse_frame, crc8

# 模拟原始载荷（源编码后）
original_bits = np.random.randint(0, 2, 100, dtype=np.int8)
# 模拟信道编码后的载荷
coded_bits = np.random.randint(0, 2, 175, dtype=np.int8)

# 组帧
frame = build_frame(original_bits, coded_bits)
print(f"帧总长度: {len(frame)} bit")

# 解帧
parsed = parse_frame(frame)
print(f"解析得到的 payload_length: {parsed['payload_length']}")
print(f"length 字段正确性: {'✅ 通过' if parsed['payload_length'] == len(original_bits) else '❌ 失败'}")

# CRC 校验
computed_crc = 0
for bit in crc8(original_bits):
    computed_crc = (computed_crc << 1) | int(bit)
print(f"CRC 校验一致性: {'✅ 通过' if computed_crc == parsed['frame_crc'] else '❌ 失败'}")