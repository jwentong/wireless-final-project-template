import csv
import json
import subprocess
import sys
from pathlib import Path


def test_experiment_runner_generates_summary_outputs(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_dir = tmp_path / "experiments"
    input_path.write_text("Experiment extension test for SNR, coding, channel, and advanced modules.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts" / "run_experiments.py"),
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--snrs",
            "6,12",
            "--seed",
            "2026",
        ],
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr

    csv_path = output_dir / "experiment_summary.csv"
    json_path = output_dir / "experiment_summary.json"
    assert csv_path.exists()
    assert json_path.exists()
    assert (output_dir / "snr_text_match.png").exists()
    assert (output_dir / "coding_gain.png").exists()

    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8")))
    assert rows
    scenarios = {row["scenario"] for row in rows}
    expected_scenarios = {
        "awgn-coded",
        "awgn-uncoded",
        "rayleigh-coded",
        "ofdm",
        "diversity-mrc2",
        "conv-viterbi",
        "adaptive-mod",
        "advanced-all",
    }
    assert expected_scenarios <= scenarios
    for scenario in expected_scenarios:
        assert (output_dir / scenario).exists()
    advanced_rows = [row for row in rows if row["scenario"] == "advanced-all"]
    assert advanced_rows
    assert {row["ofdm_enabled"] for row in advanced_rows} == {"True"}
    assert {row["diversity"] for row in advanced_rows} == {"mrc2"}
    assert {row["requested_modulation"] for row in advanced_rows} == {"adaptive"}
    assert {row["ofdm_enabled"] for row in rows if row["scenario"] == "ofdm"} == {"True"}
    assert {row["diversity"] for row in rows if row["scenario"] == "diversity-mrc2"} == {"mrc2"}
    assert {row["coding"] for row in rows if row["scenario"] == "conv-viterbi"} == {"conv"}
    assert {row["requested_modulation"] for row in rows if row["scenario"] == "adaptive-mod"} == {"adaptive"}

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert "best_required_snr_result" in summary
    assert summary["best_required_snr_result"]["snr_db"] == 12.0
    assert "advanced_high_snr_result" in summary
