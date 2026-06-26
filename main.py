"""Command-line entry point for the wireless file transmission system."""

from __future__ import annotations

import argparse

from src.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wireless baseband simulator")
    parser.add_argument("--input", required=True, help="Input UTF-8 text file")
    parser.add_argument("--output", required=True, help="Output received text file")
    parser.add_argument("--snr", type=float, default=12.0, help="SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", choices=["qpsk"], help="Modulation type")
    parser.add_argument("--channel", default="awgn", choices=["awgn", "rayleigh"], help="Channel type")
    parser.add_argument("--no-plots", action="store_true", help="Disable plot generation")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    metrics = run_pipeline(
        input_path=args.input,
        output_path=args.output,
        snr_db=args.snr,
        seed=args.seed,
        modulation=args.mod,
        channel=args.channel,
        make_plots=not args.no_plots,
    )
    print(
        "done: "
        f"text_match_rate={metrics['text_match_rate']}, "
        f"checksum_pass={metrics['checksum_pass']}, "
        f"ber={metrics['ber']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
