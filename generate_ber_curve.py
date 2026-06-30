import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from src.source_codec import text_to_bitstream
from src.scrambler import scramble, descramble
from src.channel_codec import hamming_encode, hamming_decode
from src.framer import build_frame, parse_frame
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn_channel
from src.synchronization import find_frame_start

def run_single_snr(input_text, snr_db, seed=2026):
    """运行单个SNR下的传输，返回BER"""
    original_bits = text_to_bitstream(input_text)
    
    # 发送端
    scrambled = scramble(original_bits)
    coded = hamming_encode(scrambled)
    frame_bits = build_frame(original_bits, coded)
    tx_symbols = qpsk_modulate(frame_bits)
    
    # 信道 + 随机偏移
    rng = np.random.default_rng(seed)
    offset = rng.integers(0, 129)
    prefix = rng.standard_normal(offset) + 1j * rng.standard_normal(offset)
    tx_with_offset = np.concatenate([prefix, tx_symbols])
    rx_symbols = awgn_channel(tx_with_offset, snr_db, seed)
    
    # 接收端
    sync_idx = find_frame_start(rx_symbols)
    frame_symbol_len = len(frame_bits) // 2
    frame_symbols = rx_symbols[sync_idx : sync_idx + frame_symbol_len]
    demod_bits = qpsk_demodulate(frame_symbols)
    
    parsed = parse_frame(demod_bits)
    payload_len = parsed["payload_length"]
    coded_payload = parsed["coded_payload"]
    
    decoded = hamming_decode(np.array(coded_payload, dtype=np.int8))
    descrambled = descramble(decoded)
    received_bits = descrambled[:payload_len]
    
    # 计算BER
    error = np.sum(original_bits != received_bits)
    ber = error / len(original_bits)
    return ber

if __name__ == '__main__':
    # 读取测试文本
    with open('Test.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # SNR遍历范围
    snr_list = list(range(0, 16, 2))
    ber_list = []
    
    print("开始生成 BER-SNR 曲线...")
    for snr in snr_list:
        ber = run_single_snr(text, snr, seed=2026)
        ber_list.append(ber)
        print(f"SNR = {snr:2d} dB, BER = {ber:.6f}")
    
    # 绘图
    plt.figure(figsize=(8, 5))
    plt.semilogy(snr_list, ber_list, 'o-', linewidth=1.5, markersize=5, color='#1f77b4')
    plt.xlabel('SNR (dB)')
    plt.ylabel('Bit Error Rate (BER)')
    plt.title('QPSK + Hamming(7,4) BER vs SNR Curve')
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    
    # 保存
    Path('results').mkdir(exist_ok=True)
    plt.savefig('results/ber_curve.png', dpi=150)
    plt.close()
    print("\n曲线已保存到 results/ber_curve.png")