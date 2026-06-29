"""Unified CLI entry point for the wireless baseband simulation.

Usage:
    python main.py --input Test.txt --output results/received.txt \
        --snr 12 --seed 2026 --mod qpsk --channel awgn

Generates results/received.txt, results/metrics.json and the plots
constellation.png / ber_curve.png / sync_peak.png. Runs non-interactively.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # headless plotting

import matplotlib.pyplot as plt  # noqa: E402

from src.pipeline import Config, run_end_to_end, ber_vs_snr  # noqa: E402


def _make_plots(result: dict, results_dir: Path, seed: int) -> None:
    """Generate constellation, synchronization-peak and BER-SNR plots."""
    sym = result["rx_symbols"]
    plt.figure(figsize=(5, 5))
    plt.scatter(sym.real, sym.imag, s=6, alpha=0.5, color="#2a6f78")
    plt.axhline(0, color="gray", lw=0.5)
    plt.axvline(0, color="gray", lw=0.5)
    plt.title("Received constellation")
    plt.xlabel("In-phase (I)")
    plt.ylabel("Quadrature (Q)")
    plt.tight_layout()
    plt.savefig(results_dir / "constellation.png", dpi=120)
    plt.close()

    corr = result["corr"]
    plt.figure(figsize=(7, 3))
    plt.plot(corr, color="#c2693f")
    plt.title("Preamble cross-correlation (synchronization)")
    plt.xlabel("Lag (symbols)")
    plt.ylabel("Normalized correlation")
    plt.tight_layout()
    plt.savefig(results_dir / "sync_peak.png", dpi=120)
    plt.close()

    snrs = list(range(0, 13, 2))
    uncoded, coded = ber_vs_snr(snrs, seed=seed)
    floor = 1e-6
    plt.figure(figsize=(6, 4))
    plt.semilogy(snrs, [max(b, floor) for b in uncoded], "o-", label="QPSK uncoded")
    plt.semilogy(snrs, [max(b, floor) for b in coded], "s-", label="QPSK + conv (K=7)")
    plt.grid(True, which="both", ls=":")
    plt.legend()
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title("BER vs SNR (coding gain)")
    plt.tight_layout()
    plt.savefig(results_dir / "ber_curve.png", dpi=120)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Wireless baseband file transmission simulator")
    parser.add_argument("--input", required=True, help="input UTF-8 text file")
    parser.add_argument("--output", default="results/received.txt", help="recovered text output path")
    parser.add_argument("--snr", type=float, default=12.0, help="signal-to-noise ratio in dB")
    parser.add_argument("--seed", type=int, default=2026, help="random seed for reproducibility")
    parser.add_argument("--mod", default="qpsk", help="modulation: qpsk / bpsk")
    parser.add_argument("--channel", default="awgn", help="channel: awgn / rayleigh / rician")
    parser.add_argument("--code", default="conv", help="channel code: conv / hamming")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    text = input_path.read_text(encoding="utf-8")

    cfg = Config(snr_db=args.snr, seed=args.seed, mod=args.mod, channel=args.channel, code=args.code)
    result = run_end_to_end(text, cfg)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result["received_text"], encoding="utf-8")

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "metrics.json").write_text(
        json.dumps(result["metrics"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _make_plots(result, results_dir, args.seed)

    m = result["metrics"]
    print(f"[done] text_match_rate={m['text_match_rate']:.4f} ber={m['ber']:.2e} "
          f"checksum_pass={m['checksum_pass']} sync_start_index={m['sync_start_index']}")


if __name__ == "__main__":
    main()
