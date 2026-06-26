from __future__ import annotations

import argparse
import json

from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wireless baseband file-transfer simulation")
    parser.add_argument("--input", required=True, help="UTF-8 input text file")
    parser.add_argument("--output", required=True, help="Recovered output text file")
    parser.add_argument("--snr", type=float, default=12.0, help="Symbol SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for reproducible simulation")
    parser.add_argument("--mod", default="qpsk", help="Modulation: bpsk, qpsk, 16qam, or adaptive")
    parser.add_argument("--channel", default="awgn", help="Channel: awgn or rayleigh")
    parser.add_argument("--coding", default="repetition3", help="Channel coding: repetition3, conv, or none")
    parser.add_argument("--scramble", default="pn-xor", help="Scrambler: pn-xor or none")
    parser.add_argument("--diversity", default="none", help="Receive diversity: none or mrc2")
    parser.add_argument("--ofdm", action="store_true", help="Enable OFDM with cyclic prefix")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run_pipeline(
        input_path=args.input,
        output_path=args.output,
        snr_db=args.snr,
        seed=args.seed,
        modulation=args.mod,
        channel_name=args.channel,
        scramble_mode=args.scramble,
        coding_mode=args.coding,
        diversity=args.diversity,
        ofdm_enabled=args.ofdm,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
