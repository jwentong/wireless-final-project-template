import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from src.source_codec import text_to_bitstream
from src.scrambler import scramble, descramble
from src.channel_codec import hamming_encode, hamming_decode
from src.framer import build_frame, parse_frame
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn_channel, rayleigh_channel
from src.synchronization import find_frame_start

def run_single_case(input_text, snr_db, channel_type, seed=2026):
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
    
    if channel_type == "rayleigh":
        rx_symbols = rayleigh_channel(tx_with_offset, snr_db, seed)
    else:
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
    
    error = np.sum(original_bits != received_bits)
    ber = error / len(original_bits)
    return ber

if __name__ == '__main__':
    with open('Test.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    snr_list = list(range(0, 16, 2))
    ber_awgn = []
    ber_rayleigh = []
    
    print("开始生成信道对比曲线...")
    for snr in snr_list:
        ber_awgn.append(run_single_case(text, snr, "awgn", seed=2026))
        ber_rayleigh.append(run_single_case(text, snr, "rayleigh", seed=2026))
        print(f"SNR={snr:2d}dB | AWGN BER={ber_awgn[-1]:.6f} | Rayleigh BER={ber_rayleigh[-1]:.6f}")
    
    # 绘图
    plt.figure(figsize=(8, 5))
    plt.semilogy(snr_list, ber_awgn, 'o-', linewidth=1.5, markersize=5, label='AWGN Channel')
    plt.semilogy(snr_list, ber_rayleigh, 's-', linewidth=1.5, markersize=5, label='Rayleigh Fading Channel')
    plt.xlabel('SNR (dB)')
    plt.ylabel('Bit Error Rate (BER)')
    plt.title('BER Performance Comparison: AWGN vs Rayleigh')
    plt.legend()
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    
    Path('results').mkdir(exist_ok=True)
    plt.savefig('results/ber_comparison.png', dpi=150)
    plt.close()
    print("\n对比曲线已保存到 results/ber_comparison.png")