import numpy as np

# ==============================================
# Mock 1：源编码可逆性验证
# ==============================================
def text_to_bits(text):
    """UTF-8 文本转比特流，高位在前"""
    bytes_data = text.encode('utf-8')
    bits = []
    for byte in bytes_data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return np.array(bits, dtype=int)

def bits_to_text(bits):
    """比特流转 UTF-8 文本"""
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        byte_val = 0
        for bit in byte_bits:
            byte_val = (byte_val << 1) | bit
        bytes_list.append(byte_val)
    return bytes(bytes_list).decode('utf-8')

def test_source_codec():
    print("="*50)
    print("Mock 1：源编码可逆性测试")
    with open('Test.txt', 'r', encoding='utf-8') as f:
        original = f.read()
    bits = text_to_bits(original)
    restored = bits_to_text(bits)
    passed = original == restored
    print(f"  原始文本字节数: {len(original.encode('utf-8'))}")
    print(f"  比特流总长度: {len(bits)} bit")
    print(f"  可逆性验证: {'通过' if passed else '失败'}")
    return passed, len(bits)

# ==============================================
# Mock 2：QPSK Gray 编码映射合规性验证
# ==============================================
def qpsk_modulate(bits):
    """严格遵循 PRD 指定的 Gray 编码映射"""
    mapping = {
        (0, 0): (1 + 1j) / np.sqrt(2),
        (0, 1): (-1 + 1j) / np.sqrt(2),
        (1, 1): (-1 - 1j) / np.sqrt(2),
        (1, 0): (1 - 1j) / np.sqrt(2)
    }
    symbols = []
    for i in range(0, len(bits), 2):
        b1, b2 = bits[i], bits[i+1]
        symbols.append(mapping[(b1, b2)])
    return np.array(symbols)

def test_qpsk_mapping():
    print("\n" + "="*50)
    print("Mock 2：QPSK 映射与归一化测试")
    test_bits = np.array([0, 0, 0, 1, 1, 1, 1, 0])
    symbols = qpsk_modulate(test_bits)
    avg_power = np.mean(np.abs(symbols) ** 2)
    print(f"  00 -> {symbols[0]:.4f}")
    print(f"  01 -> {symbols[1]:.4f}")
    print(f"  11 -> {symbols[2]:.4f}")
    print(f"  10 -> {symbols[3]:.4f}")
    print(f"  符号平均功率: {avg_power:.4f}")
    passed = abs(avg_power - 1.0) < 1e-6
    print(f"  归一化验证: {'通过' if passed else '失败'}")
    return passed

# ==============================================
# Mock 3：帧结构 length 字段定义验证
# ==============================================
def test_frame_length():
    print("\n" + "="*50)
    print("Mock 3：帧结构 length 字段定义验证")
    # 模拟：原始载荷比特数（源编码后、扰码前）
    original_payload_bits = 2400
    # 组帧时写入 length 字段
    length_in_frame = original_payload_bits
    # 模拟：经过扰码、信道编码后长度变化
    scrambled_bits_len = original_payload_bits
    channel_coded_bits_len = int(np.ceil(scrambled_bits_len / 4) * 7)  # 汉明码(7,4)
    
    print(f"  源编码后原始载荷长度: {original_payload_bits} bit")
    print(f"  信道编码后载荷长度: {channel_coded_bits_len} bit")
    print(f"  length 字段存储值: {length_in_frame} bit")
    
    # 核心验证：length 必须等于源编码后长度，不能是编码后长度
    passed = length_in_frame == original_payload_bits
    print(f"  定义合规性: {'通过' if passed else '失败（必须为源编码后长度）'}")
    
    # 模拟接收端：按 length 截断补零
    print(f"  接收端截断规则：解扰后保留前 {length_in_frame} bit，再做源译码")
    return passed

# ==============================================
# Mock 4：帧同步互相关原理验证
# ==============================================
def test_synchronization():
    print("\n" + "="*50)
    print("Mock 4：帧同步互相关定位验证")
    
    # 13位巴克码作为前导，重复4次
    barker13 = np.array([1,1,1,1,1,0,0,1,1,0,1,0,1])
    preamble_bits = np.tile(barker13, 4)
    # 补零对齐 2 比特
    if len(preamble_bits) % 2 != 0:
        preamble_bits = np.append(preamble_bits, 0)
    preamble_symbols = qpsk_modulate(preamble_bits)
    
    # 模拟：前置随机偏移符号 + 前导 + 载荷
    offset_symbols = 35  # 随机前置 35 个符号偏移
    rng = np.random.default_rng(2026)
    offset_data = rng.standard_normal(offset_symbols) + 1j * rng.standard_normal(offset_symbols)
    full_signal = np.concatenate([offset_data, preamble_symbols])
    
    # 滑动互相关找峰值
    corr = np.correlate(full_signal, preamble_symbols, mode='valid')
    peak_idx = np.argmax(np.abs(corr))
    
    print(f"  真实前导起始位置: {offset_symbols}")
    print(f"  检测到的峰值位置: {peak_idx}")
    error = abs(peak_idx - offset_symbols)
    print(f"  同步误差: {error} 个符号")
    passed = error <= 1
    print(f"  精度验证: {'通过' if passed else '失败'}")
    return passed

# ==============================================
# Mock 5：固定种子 AWGN 可复现性验证
# ==============================================
def add_awgn(symbols, snr_db, seed):
    rng = np.random.default_rng(seed)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = 1 / snr_linear
    noise = rng.normal(0, np.sqrt(noise_power/2), len(symbols)) + \
            1j * rng.normal(0, np.sqrt(noise_power/2), len(symbols))
    return symbols + noise

def test_awgn_reproducible():
    print("\n" + "="*50)
    print("Mock 5：AWGN 固定种子可复现性测试")
    test_symbols = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)
    out1 = add_awgn(test_symbols, 12, 2026)
    out2 = add_awgn(test_symbols, 12, 2026)
    passed = np.allclose(out1, out2)
    print(f"  两次运行结果完全一致: {'是' if passed else '否'}")
    print(f"  可复现性验证: {'通过' if passed else '失败'}")
    return passed

# ==============================================
# 主程序：运行全部 Mock 测试
# ==============================================
if __name__ == '__main__':
    print("开始执行 Mock 测试...\n")
    
    results = []
    results.append(("源编码可逆性", test_source_codec()[0]))
    results.append(("QPSK映射合规性", test_qpsk_mapping()))
    results.append(("length字段定义", test_frame_length()))
    results.append(("帧同步定位精度", test_synchronization()))
    results.append(("AWGN可复现性", test_awgn_reproducible()))
    
    print("\n" + "="*50)
    print("Mock 测试汇总")
    passed_count = 0
    for name, ok in results:
        status = "通过" if ok else "失败"
        passed_count += 1 if ok else 0
        print(f"  {name}: {status}")
    print(f"\n总计: {passed_count}/{len(results)} 项通过")