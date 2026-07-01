import argparse
import numpy as np
from pathlib import Path

from src.source_codec import text_to_bitstream, bitstream_to_text
from src.scrambler import scramble, descramble
from src.channel_codec import hamming_encode, hamming_decode
from src.framer import build_frame, parse_frame, crc8, PREAMBLE_LEN
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn_channel, rayleigh_channel
from src.synchronization import find_frame_start, LOCAL_PREAMBLE_SYMBOLS
from src.metrics import calculate_metrics, save_metrics_json
from src.metrics import plot_constellation, plot_sync_peak, plot_ber_curve


def main():
    parser = argparse.ArgumentParser(description='Wireless Communication Baseband Simulation System')
    parser.add_argument('--input', type=str, default='Test.txt', help='Input text file')
    parser.add_argument('--output', type=str, default='results/received.txt', help='Output received text file')
    parser.add_argument('--snr', type=float, default=12, help='SNR in dB')
    parser.add_argument('--seed', type=int, default=2026, help='Random seed')
    parser.add_argument('--mod', type=str, default='qpsk', help='Modulation type')
    parser.add_argument('--channel', type=str, default='awgn', help='Channel type')
    args = parser.parse_args()

    # 读取输入文件
    with open(args.input, 'r', encoding='utf-8') as f:
        original_text = f.read()
    original_bits = text_to_bitstream(original_text)

    # ====================== 发送端 ======================
    # 1. 扰码
    scrambled_bits = scramble(original_bits)
    # 2. 信道编码
    coded_bits = hamming_encode(scrambled_bits)
    # 3. 组帧
    frame_bits = build_frame(original_bits, coded_bits)
    # 4. QPSK调制
    tx_symbols = qpsk_modulate(frame_bits)

    # ====================== 信道 ======================
    rng = np.random.default_rng(args.seed)
    # 随机前置偏移：0~128个符号
    offset_symbols = rng.integers(0, 129)
    prefix_noise = rng.standard_normal(offset_symbols) + 1j * rng.standard_normal(offset_symbols)
    tx_with_offset = np.concatenate([prefix_noise, tx_symbols])
    
    # 根据参数选择信道类型
    if args.channel == "rayleigh":
        rx_symbols = rayleigh_channel(tx_with_offset, args.snr, args.seed)
    else:
        # 默认 AWGN 信道
        rx_symbols = awgn_channel(tx_with_offset, args.snr, args.seed)

    # ====================== 接收端 ======================
    # 1. 帧同步
    sync_start_idx = find_frame_start(rx_symbols)
    # 计算相关值用于绘图
    corr_values = np.correlate(rx_symbols, LOCAL_PREAMBLE_SYMBOLS, mode='valid')
    # 截取完整帧符号
    frame_symbol_len = len(frame_bits) // 2
    frame_symbols = rx_symbols[sync_start_idx : sync_start_idx + frame_symbol_len]

    # 2. QPSK解调
    demod_bits = qpsk_demodulate(frame_symbols)

    # 3. 解帧
    parsed = parse_frame(demod_bits)
    payload_length = parsed["payload_length"]
    coded_payload = parsed["coded_payload"]
    frame_crc = parsed["frame_crc"]

    # 4. 信道译码
    decoded_bits = hamming_decode(coded_payload)

    # 5. 解扰
    descrambled_bits = descramble(decoded_bits)

    # 6. 按length截断有效比特
    received_payload_bits = descrambled_bits[:payload_length]

    # 7. CRC校验
    computed_crc = 0
    for bit in crc8(original_bits):
        computed_crc = (computed_crc << 1) | int(bit)
    checksum_pass = (computed_crc == frame_crc)

    # 8. 源译码
    received_text = bitstream_to_text(received_payload_bits)

    # 保存输出文件
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(received_text)

    # 计算并保存性能指标
    metrics = calculate_metrics(
        original_bits, received_payload_bits,
        original_text, received_text,
        checksum_pass, sync_start_idx,
        args.snr, args.seed, args.mod, args.channel
    )
    save_metrics_json(metrics, 'results/metrics.json')

    # 生成可视化图表
    plot_constellation(rx_symbols, 'results/constellation.png')
    plot_sync_peak(corr_values, sync_start_idx, 'results/sync_peak.png')

    # 打印结果
    print(f"传输完成")
    print(f"SNR: {args.snr} dB")
    print(f"BER: {metrics['ber']:.6f}")
    print(f"文本匹配率: {metrics['text_match_rate']:.4f}")
    print(f"校验结果: {'通过' if checksum_pass else '失败'}")
    print(f"同步起始索引: {sync_start_idx}")


if __name__ == '__main__':
    main()