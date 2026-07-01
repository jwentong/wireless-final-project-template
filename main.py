#!/usr/bin/env python3
"""无线通信基带仿真系统 - 统一命令行入口

链路: Test.txt -> Source Encode -> Scramble -> Channel Encode -> Frame Build
      -> QPSK Modulate -> Channel(AWGN) -> Synchronization -> QPSK Demodulate
      -> Frame Parse -> Channel Decode -> Descramble -> Source Decode -> received.txt
"""
import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.source import source_encode, source_decode
from src.scramble import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame, PREAMBLE_BITS
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn
from src.synchronization import synchronize
from src.metrics import bit_error_rate, text_match_rate as compute_text_match_rate
from src.plotting import plot_constellation, plot_ber_curve, plot_sync_peak

SYNC_OFFSET_SYMBOLS = 25  # 默认同步前置偏移符号数（呼应 PRD 示例 sync_start_index=25）


def _bits_checksum16(bits):
    """对比特序列计算 16 位 CRC 校验值，用于端到端(FEC 纠错后)完整性核对。"""
    bits = list(bits)
    pad = (-len(bits)) % 8
    bits = bits + [0] * pad
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i : i + 8]:
            byte = (byte << 1) | int(b)
        data.append(byte)
    return zlib.crc32(bytes(data)) & 0xFFFF


def parse_args():
    parser = argparse.ArgumentParser(description="无线通信基带仿真系统")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--snr", type=float, default=12.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--mod", default="qpsk", choices=["qpsk"])
    parser.add_argument("--channel", default="awgn", choices=["awgn"])
    return parser.parse_args()


def pad_to_even(bits):
    return bits + [0] if len(bits) % 2 else bits


def preamble_symbols():
    return qpsk_modulate(PREAMBLE_BITS)


def transmit(text, seed):
    src_bits = source_encode(text)
    scrambled = scramble(src_bits, seed=seed)
    coded = channel_encode(scrambled)
    frame_bits = build_frame(coded)
    padded_bits = pad_to_even(frame_bits)
    symbols = qpsk_modulate(padded_bits)
    checksum_ref = _bits_checksum16(scrambled)
    return symbols, len(src_bits), coded, checksum_ref


def add_sync_offset(symbols, seed, n_offset=SYNC_OFFSET_SYMBOLS):
    rng = np.random.default_rng(seed + 777)
    prefix = (rng.normal(size=n_offset) + 1j * rng.normal(size=n_offset)) / np.sqrt(2)
    return np.concatenate([prefix, symbols])


def receive(received_symbols, seed):
    p_syms = preamble_symbols()
    start = synchronize(received_symbols, preamble=p_syms)
    aligned = received_symbols[start:]
    demod_bits = qpsk_demodulate(aligned)
    parsed = parse_frame(demod_bits)
    coded_payload = parsed["payload"]
    frame_checksum_pass = parsed["checksum_pass"]
    scrambled = channel_decode(coded_payload)
    checksum_rx = _bits_checksum16(scrambled)
    src_bits = descramble(scrambled, seed=seed)
    try:
        text = source_decode(src_bits)
    except Exception:
        n = (len(src_bits) // 8) * 8
        data = bytearray()
        for i in range(0, n, 8):
            byte = 0
            for b in src_bits[i : i + 8]:
                byte = (byte << 1) | int(b)
            data.append(byte)
        text = bytes(data).decode("utf-8", errors="replace")
    return text, start, frame_checksum_pass, checksum_rx, coded_payload


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = input_path.read_text(encoding="utf-8")

    tx_symbols, src_len, coded_ref, checksum_ref = transmit(text, args.seed)
    offset_symbols = add_sync_offset(tx_symbols, args.seed)
    rx_symbols = awgn(offset_symbols, snr_db=args.snr, seed=args.seed)

    recovered_text, sync_start, frame_checksum_pass, checksum_rx, coded_payload = receive(
        rx_symbols, args.seed
    )
    checksum_pass = checksum_rx == checksum_ref

    output_path.write_text(recovered_text, encoding="utf-8")

    ber = bit_error_rate(coded_ref, coded_payload)
    fer = 0.0 if list(coded_ref) == list(coded_payload) else 1.0
    match_rate = compute_text_match_rate(text, recovered_text)

    metrics = {
        "snr_db": args.snr,
        "seed": args.seed,
        "modulation": args.mod,
        "channel": args.channel,
        "payload_bits": src_len,
        "ber": ber,
        "fer": fer,
        "text_match_rate": match_rate,
        "checksum_pass": bool(checksum_pass),
        "sync_start_index": int(sync_start),
    }

    results_dir = output_path.parent
    with open(results_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    try:
        plot_constellation(rx_symbols[SYNC_OFFSET_SYMBOLS:SYNC_OFFSET_SYMBOLS + 300], results_dir / "constellation.png")
        plot_ber_curve(results_dir / "ber_curve.png", seed=args.seed)
        plot_sync_peak(rx_symbols, preamble_symbols(), results_dir / "sync_peak.png")
    except Exception as exc:  # 绘图失败不应影响主流程判定
        print(f"[WARN] plotting failed: {exc}", file=sys.stderr)

    print(
        f"[OK] text_match_rate={match_rate:.4f} ber={ber:.6f} "
        f"fer={fer} checksum_pass={checksum_pass} sync_start_index={sync_start}"
    )


if __name__ == "__main__":
    main()
