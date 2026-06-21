import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt

from src.source_codec import SourceCodec
from src.scrambler import Scrambler
from src.channel_coding import ChannelCodec
from src.frame import Framer
from src.modem import QPSKModem
from src.channel import AWGNChannel
from src.sync import Synchronizer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    parser.add_argument('--snr', type=float, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--mod', type=str, required=True)
    parser.add_argument('--channel', type=str, required=True)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            original_text = f.read()
        src_bits = SourceCodec.encode(original_text)
        
        scrambled_bits = Scrambler.process(src_bits, args.seed)
        payload_bits_len = len(scrambled_bits)
        
        encoded_bits = ChannelCodec.encode(scrambled_bits)
        frame_bits = Framer.build_frame(encoded_bits)
        tx_symbols = QPSKModem.modulate(frame_bits)
        rx_symbols, actual_offset = AWGNChannel.pass_channel(tx_symbols, args.snr, args.seed)
        
        synced_symbols, sync_start_index, correlations = Synchronizer.sync(rx_symbols)
        demodulated_bits = QPSKModem.demodulate(synced_symbols)
        
        payload_rx, length_field, checksum_pass = Framer.parse_frame(demodulated_bits)
        decoded_bits = ChannelCodec.decode(payload_rx)
        
        # 安全处理截断，防止误码导致的长度不一
        if len(decoded_bits) < payload_bits_len:
            decoded_bits = np.pad(decoded_bits, (0, payload_bits_len - len(decoded_bits)), 'constant')
        else:
            decoded_bits = decoded_bits[:payload_bits_len]
            
        descrambled_bits = Scrambler.process(decoded_bits, args.seed)
        recovered_text = SourceCodec.decode(descrambled_bits)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(recovered_text)

        ber = float(np.mean(src_bits != descrambled_bits)) if len(descrambled_bits) == len(src_bits) else 1.0
        text_match_rate = 1.0 if original_text == recovered_text else 0.0

        metrics = {
            "snr_db": args.snr,
            "seed": args.seed,
            "modulation": args.mod,
            "channel": args.channel,
            "payload_bits": payload_bits_len,
            "ber": ber,
            "fer": 0.0 if checksum_pass else 1.0,
            "text_match_rate": text_match_rate,
            "checksum_pass": bool(checksum_pass),
            "sync_start_index": int(sync_start_index)
        }

        with open('results/metrics.json', 'w') as f:
            json.dump(metrics, f, indent=4)

        plt.figure()
        plt.scatter(synced_symbols.real, synced_symbols.imag, s=1, alpha=0.5)
        plt.title(f"QPSK Constellation (SNR={args.snr}dB)")
        plt.xlabel("I")
        plt.ylabel("Q")
        plt.grid(True)
        plt.savefig('results/constellation.png')
        plt.close()

        plt.figure()
        plt.plot(correlations)
        plt.title("Synchronization Cross-Correlation")
        plt.xlabel("Sample Index")
        plt.ylabel("Magnitude")
        plt.grid(True)
        plt.savefig('results/sync_peak.png')
        plt.close()

        print(f"[SUCCESS] 仿真完成。BER: {ber:.4f}, CRC: {checksum_pass}")

    except Exception as e:
        print(f"[ERROR] 系统崩溃或异常: {e}")
        with open('results/metrics.json', 'w') as f:
            json.dump({"ber": 1.0, "fer": 1.0, "text_match_rate": 0.0, "checksum_pass": False}, f)

if __name__ == "__main__":
    main()
