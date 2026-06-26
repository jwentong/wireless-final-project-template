#!/usr/bin/env python3
"""Wireless Communication Baseband Simulation System.

Unified CLI entry point for the end-to-end wireless communication pipeline.

Usage:
    python main.py --input Test.txt --output results/received.txt \\
                   --snr 12 --seed 2026 --mod qpsk --channel awgn

Pipeline:
    Test.txt → Source Encode → Scramble → Channel Encode → Frame Build
    → QPSK Modulate → Channel (AWGN) → Synchronization → QPSK Demodulate
    → Frame Parse → Channel Decode → Descramble → Source Decode → Received.txt
    → Metrics / Plots
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

from src.source import text_to_bits, bits_to_text
from src.crypto import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame
from src.modulation import modulate, demodulate
from src.channel import awgn, rayleigh
from src.synchronization import synchronize
from src.metrics import compute_ber, compute_fer, compute_text_match
from src.plots import plot_constellation, plot_ber_curve, plot_sync_peak


def run_pipeline(input_path: str, output_path: str, snr_db: float, seed: int,
                 mod_type: str, channel_type: str):
    """Run the full end-to-end wireless communication pipeline.

    Args:
        input_path: Path to input UTF-8 text file.
        output_path: Path to output recovered text file.
        snr_db: SNR in dB.
        seed: Random seed for reproducibility.
        mod_type: Modulation type ("qpsk", "bpsk", "qam16").
        channel_type: Channel type ("awgn", "rayleigh").

    Returns:
        Dictionary of metrics.
    """
    # ============================================================
    # 1. Source Encode: Read text and convert to bits
    # ============================================================
    input_text = Path(input_path).read_text(encoding="utf-8")
    original_bits = text_to_bits(input_text)
    payload_bits_count = len(original_bits)

    # ============================================================
    # 2. Scramble: XOR with PN sequence
    # ============================================================
    scrambled_bits = scramble(original_bits, seed=seed)

    # ============================================================
    # 3. Channel Encode: Convolutional encoding
    # ============================================================
    encoded_bits = channel_encode(scrambled_bits)

    # ============================================================
    # 4. Frame Build: Add preamble, length, checksum
    # ============================================================
    frame_bits = build_frame(encoded_bits, original_payload_bits=payload_bits_count)

    # ============================================================
    # 5. Modulate: Map bits to symbols
    # ============================================================
    symbols = modulate(frame_bits, mod_type=mod_type)

    # ============================================================
    # 6. Channel: Add noise/fading
    # ============================================================
    if channel_type == "rayleigh":
        noisy_symbols, channel_coeffs = rayleigh(symbols, snr_db=snr_db, seed=seed)
    else:
        noisy_symbols = awgn(symbols, snr_db=snr_db, seed=seed)

    # ============================================================
    # 7. Synchronization: Detect frame start
    # ============================================================
    # Generate preamble symbols (same m-sequence as framing.py)
    from src.framing import PREAMBLE_BITS as _PB
    preamble_syms = modulate(list(_PB), mod_type=mod_type)

    sync_result = synchronize(noisy_symbols, preamble=preamble_syms)
    sync_start = sync_result.get("start_index", 0)
    correlation = sync_result.get("correlation", [])

    # Extract frame starting from detected position
    aligned_symbols = noisy_symbols[sync_start:]

    # ============================================================
    # 8. Demodulate: Map symbols back to bits
    # ============================================================
    recovered_frame_bits = demodulate(aligned_symbols, mod_type=mod_type)

    # ============================================================
    # 9. Frame Parse: Extract payload, verify checksum
    # ============================================================
    parsed = parse_frame(recovered_frame_bits)
    recovered_encoded_bits = parsed.get("payload", [])
    checksum_pass = parsed.get("checksum_pass", False)
    length_field = parsed.get("length", 0)

    # ============================================================
    # 10. Channel Decode: Viterbi decoding
    # ============================================================
    recovered_scrambled_bits = channel_decode(recovered_encoded_bits)

    # ============================================================
    # 11. Descramble: Reverse XOR with PN sequence
    # ============================================================
    recovered_bits = descramble(recovered_scrambled_bits, seed=seed)

    # Trim to original payload length
    recovered_bits = recovered_bits[:payload_bits_count]

    # ============================================================
    # 12. Source Decode: Convert bits back to text
    # ============================================================
    recovered_text = bits_to_text(recovered_bits)

    # ============================================================
    # Write output
    # ============================================================
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(recovered_text, encoding="utf-8")

    # ============================================================
    # Compute metrics
    # ============================================================
    ber = compute_ber(original_bits, recovered_bits)
    fer = compute_fer(original_bits, recovered_bits)
    text_match = compute_text_match(input_text, recovered_text)

    # Verify checksum: compute original payload checksum
    original_bytes = input_text.encode("utf-8")
    original_checksum = sum(original_bytes) & 0xFFFF
    recovered_bytes = recovered_text.encode("utf-8")
    recovered_checksum = sum(recovered_bytes) & 0xFFFF
    final_checksum_pass = checksum_pass and (original_checksum == recovered_checksum)

    metrics = {
        "snr_db": snr_db,
        "seed": seed,
        "modulation": mod_type,
        "channel": channel_type,
        "payload_bits": payload_bits_count,
        "ber": ber,
        "fer": fer,
        "text_match_rate": text_match,
        "checksum_pass": final_checksum_pass,
        "sync_start_index": sync_start,
    }

    # Write metrics
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # ============================================================
    # Generate plots
    # ============================================================
    # 1. Constellation diagram
    plot_constellation(
        noisy_symbols,
        output_path=str(output_dir / "constellation.png"),
        title=f"QPSK Constellation (SNR={snr_db}dB, {channel_type.upper()})"
    )

    # 2. BER curve (sweep SNR values)
    if mod_type == "qpsk" and channel_type == "awgn":
        snr_sweep = list(range(0, 21, 2))  # 0, 2, 4, ..., 20 dB
        ber_sweep = []
        for s in snr_sweep:
            # Run a quick BER measurement at each SNR
            test_syms = modulate(frame_bits, mod_type=mod_type)
            test_noisy = awgn(test_syms, snr_db=s, seed=seed + s)
            test_aligned = test_noisy[sync_start:]
            test_frame_bits = demodulate(test_aligned, mod_type=mod_type)
            test_parsed = parse_frame(test_frame_bits)
            test_enc = test_parsed.get("payload", [])
            test_dec = channel_decode(test_enc)
            test_desc = descramble(test_dec, seed=seed)[:payload_bits_count]
            ber_s = compute_ber(original_bits, test_desc)
            ber_sweep.append(ber_s)
        plot_ber_curve(
            [float(s) for s in snr_sweep],
            [float(b) for b in ber_sweep],
            output_path=str(output_dir / "ber_curve.png"),
            title=f"BER vs SNR ({mod_type.upper()}, {channel_type.upper()} Channel)"
        )
    else:
        # Generate a basic BER curve even for other modulations
        snr_sweep = list(range(0, 21, 2))
        ber_sweep = []
        for s in snr_sweep:
            test_syms = modulate(frame_bits, mod_type=mod_type)
            if channel_type == "rayleigh":
                test_noisy, _ = rayleigh(test_syms, snr_db=s, seed=seed + s)
            else:
                test_noisy = awgn(test_syms, snr_db=s, seed=seed + s)
            test_aligned = test_noisy[sync_start:]
            test_frame_bits = demodulate(test_aligned, mod_type=mod_type)
            test_parsed = parse_frame(test_frame_bits)
            test_enc = test_parsed.get("payload", [])
            test_dec = channel_decode(test_enc)
            test_desc = descramble(test_dec, seed=seed)[:payload_bits_count]
            ber_s = compute_ber(original_bits, test_desc)
            ber_sweep.append(ber_s)
        plot_ber_curve(
            [float(s) for s in snr_sweep],
            [float(b) for b in ber_sweep],
            output_path=str(output_dir / "ber_curve.png"),
            title=f"BER vs SNR ({mod_type.upper()}, {channel_type.upper()} Channel)"
        )

    # 3. Synchronization correlation peak
    plot_sync_peak(
        correlation,
        start_index=sync_start,
        output_path=str(output_dir / "sync_peak.png"),
        title="Synchronization Cross-Correlation Peak"
    )

    return metrics


def main():
    """Parse CLI arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        description="Wireless Communication Baseband Simulation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  python main.py --input Test.txt --output results/received.txt \\
                 --snr 12 --seed 2026 --mod qpsk --channel awgn
        """
    )
    parser.add_argument("--input", type=str, default="Test.txt",
                        help="Path to input UTF-8 text file (default: Test.txt)")
    parser.add_argument("--output", type=str, default="results/received.txt",
                        help="Path to output recovered text file (default: results/received.txt)")
    parser.add_argument("--snr", type=float, default=12.0,
                        help="SNR in dB (default: 12.0)")
    parser.add_argument("--seed", type=int, default=2026,
                        help="Random seed for reproducibility (default: 2026)")
    parser.add_argument("--mod", type=str, default="qpsk",
                        choices=["qpsk", "bpsk", "qam16"],
                        help="Modulation type (default: qpsk)")
    parser.add_argument("--channel", type=str, default="awgn",
                        choices=["awgn", "rayleigh"],
                        help="Channel type (default: awgn)")

    args = parser.parse_args()

    # Set matplotlib backend to non-interactive
    os.environ.setdefault("MPLBACKEND", "Agg")

    print(f"Wireless Communication Baseband Simulation System")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  SNR: {args.snr} dB")
    print(f"  Seed: {args.seed}")
    print(f"  Modulation: {args.mod}")
    print(f"  Channel: {args.channel}")
    print()

    try:
        metrics = run_pipeline(
            input_path=args.input,
            output_path=args.output,
            snr_db=args.snr,
            seed=args.seed,
            mod_type=args.mod,
            channel_type=args.channel,
        )

        print("Pipeline completed successfully.")
        print(f"  Payload bits: {metrics['payload_bits']}")
        print(f"  BER: {metrics['ber']:.6f}")
        print(f"  FER: {metrics['fer']:.6f}")
        print(f"  Text match rate: {metrics['text_match_rate']:.2f}")
        print(f"  Checksum pass: {metrics['checksum_pass']}")
        print(f"  Sync start index: {metrics['sync_start_index']}")
        print(f"  Output written to: {args.output}")
        print(f"  Metrics written to: results/metrics.json")
        print(f"  Plots saved to: results/")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
