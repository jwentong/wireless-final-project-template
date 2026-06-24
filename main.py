#!/usr/bin/env python3
"""Wireless communication baseband simulation CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from src.channel import awgn, rayleigh
from src.metrics import build_metrics, save_metrics
from src.plots import generate_all_plots
from src.receiver import run_receiver
from src.transmitter import run_transmitter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wireless baseband file transfer simulation")
    parser.add_argument("--input", default="Test.txt", help="Input UTF-8 text file")
    parser.add_argument("--output", default="results/received.txt", help="Output recovered text file")
    parser.add_argument("--snr", type=float, default=12.0, help="SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", choices=["qpsk"], help="Modulation scheme")
    parser.add_argument("--channel", default="awgn", choices=["awgn", "rayleigh"], help="Channel model")
    parser.add_argument("--fec", default="repeat", choices=["repeat", "conv"], help="FEC mode (repeat=default)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    results_dir = output_path.parent
    results_dir.mkdir(parents=True, exist_ok=True)

    text = input_path.read_text(encoding="utf-8")
    tx_symbols, meta = run_transmitter(text, seed=args.seed)

    if args.channel == "rayleigh":
        rx_symbols, _ = rayleigh(tx_symbols, snr_db=args.snr, seed=args.seed)
    else:
        rx_symbols = awgn(tx_symbols, snr_db=args.snr, seed=args.seed)

    recovered, partial = run_receiver(
        rx_symbols,
        seed=args.seed,
        preamble_symbols=meta["preamble_symbols"],
        original_text=text,
    )

    output_path.write_text(recovered, encoding="utf-8")

    sync_corr = partial.get("sync", {}).get("correlation", np.array([]))
    if hasattr(sync_corr, "tolist"):
        sync_corr = np.asarray(sync_corr)

    metrics = build_metrics(
        snr_db=args.snr,
        seed=args.seed,
        modulation=args.mod,
        channel=args.channel,
        payload_bits=int(partial["payload_bits"]),
        ber=float(partial["ber"]),
        fer=float(partial["fer"]),
        text_match_rate=float(partial["text_match_rate"]),
        checksum_pass=bool(partial["checksum_pass"]),
        sync_start_index=int(partial["sync_start_index"]),
        failure_reason=partial.get("failure_reason"),
        fec=args.fec,
    )
    save_metrics(metrics, results_dir / "metrics.json")

    generate_all_plots(
        text=text,
        seed=args.seed,
        snr_db=args.snr,
        results_dir=results_dir,
        rx_symbols=rx_symbols,
        sync_correlation=sync_corr,
        sync_start_index=int(partial["sync_start_index"]),
        channel_name=args.channel,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
