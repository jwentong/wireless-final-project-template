from __future__ import annotations

import argparse
import sys

from src.pipeline import run_system


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wireless baseband file transmission simulation.")
    parser.add_argument("--input", default="Test.txt", help="UTF-8 input text file.")
    parser.add_argument("--output", default="results/received.txt", help="Recovered output text file.")
    parser.add_argument("--snr", type=float, default=12.0, help="AWGN SNR in dB.")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for reproducible simulation.")
    parser.add_argument("--mod", default="qpsk", choices=["qpsk"], help="Modulation scheme.")
    parser.add_argument("--channel", default="awgn", choices=["awgn", "rayleigh"], help="Channel model.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metrics = run_system(
            input_path=args.input,
            output_path=args.output,
            snr_db=args.snr,
            seed=args.seed,
            modulation=args.mod,
            channel=args.channel,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        "BER={ber:.6g} FER={fer:.6g} text_match_rate={tmr:.6g} "
        "checksum_pass={checksum} output={output}".format(
            ber=float(metrics.get("ber", 1.0)),
            fer=float(metrics.get("fer", 1.0)),
            tmr=float(metrics.get("text_match_rate", 0.0)),
            checksum=bool(metrics.get("checksum_pass", False)),
            output=args.output,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
