from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline import run_transmission


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wireless communication baseband simulation")
    parser.add_argument("--input", required=True, help="Input UTF-8 text file")
    parser.add_argument("--output", required=True, help="Recovered output text file")
    parser.add_argument("--snr", type=float, default=12.0, help="AWGN SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", help="Modulation, baseline supports qpsk")
    parser.add_argument("--channel", default="awgn", help="Channel, baseline supports awgn")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run_transmission(
        input_path=args.input,
        output_path=args.output,
        snr_db=args.snr,
        seed=args.seed,
        modulation=args.mod,
        channel_name=args.channel,
    )
    output_path = Path(args.output)
    metrics_path = output_path.parent / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Wrote {metrics_path}")
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

