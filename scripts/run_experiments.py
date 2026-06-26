from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.pipeline import run_pipeline


SCENARIOS = [
    {
        "name": "awgn-coded",
        "channel": "awgn",
        "coding": "repetition3",
        "scramble": "pn-xor",
        "modulation": "qpsk",
        "diversity": "none",
        "ofdm": False,
        "description": "Required baseline with repetition-3 coding.",
    },
    {
        "name": "awgn-uncoded",
        "channel": "awgn",
        "coding": "none",
        "scramble": "pn-xor",
        "modulation": "qpsk",
        "diversity": "none",
        "ofdm": False,
        "description": "Ablation study: disables FEC to show coding gain.",
    },
    {
        "name": "rayleigh-coded",
        "channel": "rayleigh",
        "coding": "repetition3",
        "scramble": "pn-xor",
        "modulation": "qpsk",
        "diversity": "none",
        "ofdm": False,
        "description": "Level 3 fading-channel extension with one-tap equalization.",
    },
    {
        "name": "ofdm",
        "channel": "awgn",
        "coding": "repetition3",
        "scramble": "pn-xor",
        "modulation": "qpsk",
        "diversity": "none",
        "ofdm": True,
        "description": "Split Level 3 evidence: OFDM with FFT 64 and cyclic prefix 16.",
    },
    {
        "name": "diversity-mrc2",
        "channel": "rayleigh",
        "coding": "repetition3",
        "scramble": "pn-xor",
        "modulation": "qpsk",
        "diversity": "mrc2",
        "ofdm": False,
        "description": "Split Level 3 evidence: two-branch Rayleigh MRC receive diversity.",
    },
    {
        "name": "conv-viterbi",
        "channel": "awgn",
        "coding": "conv",
        "scramble": "pn-xor",
        "modulation": "qpsk",
        "diversity": "none",
        "ofdm": False,
        "description": "Split Level 3 evidence: convolutional coding with Viterbi decoding.",
    },
    {
        "name": "adaptive-mod",
        "channel": "awgn",
        "coding": "repetition3",
        "scramble": "pn-xor",
        "modulation": "adaptive",
        "diversity": "none",
        "ofdm": False,
        "description": "Split Level 3 evidence: SNR-based adaptive BPSK/QPSK/16-QAM modulation.",
    },
    {
        "name": "advanced-all",
        "channel": "rayleigh",
        "coding": "conv",
        "scramble": "pn-xor",
        "modulation": "adaptive",
        "diversity": "mrc2",
        "ofdm": True,
        "description": "All advanced modules: adaptive modulation, convolutional Viterbi, OFDM, and MRC2 diversity.",
    },
]


def parse_snr_list(value: str) -> list[float]:
    snrs = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not snrs:
        raise argparse.ArgumentTypeError("at least one SNR value is required")
    return snrs


def run_experiments(input_path: Path, output_dir: Path, snrs: list[float], seed: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        for snr in snrs:
            run_dir = output_dir / scenario["name"] / f"snr_{snr:g}"
            output_path = run_dir / "received.txt"
            metrics = run_pipeline(
                input_path=input_path,
                output_path=output_path,
                snr_db=snr,
                seed=seed,
                modulation=str(scenario["modulation"]),
                channel_name=str(scenario["channel"]),
                source_codec="utf8",
                scramble_mode=str(scenario["scramble"]),
                coding_mode=str(scenario["coding"]),
                diversity=str(scenario["diversity"]),
                ofdm_enabled=bool(scenario["ofdm"]),
            )
            rows.append(
                {
                    "scenario": scenario["name"],
                    "description": scenario["description"],
                    "snr_db": float(snr),
                    "channel": metrics["channel"],
                    "coding": scenario["coding"],
                    "scramble": scenario["scramble"],
                    "requested_modulation": metrics["requested_modulation"],
                    "effective_modulation": metrics["effective_modulation"],
                    "ofdm_enabled": metrics["ofdm_enabled"],
                    "diversity": metrics["diversity"],
                    "ber": float(metrics["ber"]),
                    "fer": float(metrics["fer"]),
                    "text_match_rate": float(metrics["text_match_rate"]),
                    "checksum_pass": bool(metrics["checksum_pass"]),
                    "sync_error_symbols": int(metrics["sync_error_symbols"]),
                    "received_path": str(output_path),
                }
            )
    return rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    fieldnames = [
        "scenario",
        "description",
        "snr_db",
        "channel",
        "coding",
        "scramble",
        "requested_modulation",
        "effective_modulation",
        "ofdm_enabled",
        "diversity",
        "ber",
        "fer",
        "text_match_rate",
        "checksum_pass",
        "sync_error_symbols",
        "received_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]], snrs: list[float]) -> dict[str, object]:
    required_snr = 12.0 if 12.0 in snrs else max(snrs)
    baseline = [
        row for row in rows
        if row["scenario"] == "awgn-coded" and float(row["snr_db"]) == required_snr
    ]
    advanced = [
        row for row in rows
        if row["scenario"] == "advanced-all" and float(row["snr_db"]) == max(snrs)
    ]
    best_required = baseline[0] if baseline else {}
    by_scenario: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_scenario.setdefault(str(row["scenario"]), []).append(row)
    return {
        "purpose": "Evidence for SNR degradation, coding gain, Rayleigh extension, and all Level 3 advanced modules.",
        "best_required_snr_result": best_required,
        "advanced_high_snr_result": advanced[0] if advanced else {},
        "scenario_count": len(by_scenario),
        "snrs": snrs,
        "scenarios": {scenario["name"]: scenario["description"] for scenario in SCENARIOS},
    }


def plot_text_match(rows: list[dict[str, object]], output_dir: Path) -> None:
    plt.figure(figsize=(7, 4))
    for scenario in sorted({str(row["scenario"]) for row in rows}):
        series = sorted([row for row in rows if row["scenario"] == scenario], key=lambda item: float(item["snr_db"]))
        plt.plot(
            [float(row["snr_db"]) for row in series],
            [float(row["text_match_rate"]) for row in series],
            marker="o",
            label=scenario,
        )
    plt.xlabel("SNR (dB)")
    plt.ylabel("Text match rate")
    plt.title("Text Recovery vs SNR")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "snr_text_match.png", dpi=150)
    plt.close()


def plot_coding_gain(rows: list[dict[str, object]], output_dir: Path) -> None:
    coded = sorted([row for row in rows if row["scenario"] == "awgn-coded"], key=lambda item: float(item["snr_db"]))
    uncoded = sorted([row for row in rows if row["scenario"] == "awgn-uncoded"], key=lambda item: float(item["snr_db"]))
    plt.figure(figsize=(7, 4))
    if coded:
        plt.semilogy(
            [float(row["snr_db"]) for row in coded],
            [max(float(row["ber"]), 1e-5) for row in coded],
            marker="o",
            label="coded repetition-3",
        )
    if uncoded:
        plt.semilogy(
            [float(row["snr_db"]) for row in uncoded],
            [max(float(row["ber"]), 1e-5) for row in uncoded],
            marker="s",
            label="uncoded",
        )
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title("Coding Gain Evidence")
    plt.grid(True, which="both", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "coding_gain.png", dpi=150)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run extension experiments for defense evidence.")
    parser.add_argument("--input", default="Test.txt", help="Input UTF-8 text file.")
    parser.add_argument("--output-dir", default="results/experiments", help="Directory for experiment outputs.")
    parser.add_argument("--snrs", type=parse_snr_list, default=parse_snr_list("0,3,6,9,12,15,24"))
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    rows = run_experiments(input_path=input_path, output_dir=output_dir, snrs=args.snrs, seed=args.seed)
    write_csv(rows, output_dir / "experiment_summary.csv")
    summary = summarize(rows, args.snrs)
    (output_dir / "experiment_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_text_match(rows, output_dir)
    plot_coding_gain(rows, output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
