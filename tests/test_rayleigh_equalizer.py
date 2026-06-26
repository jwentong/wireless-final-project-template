import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from src.channel import estimate_flat_channel, rayleigh_flat


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_rayleigh_flat_reproducible_with_fixed_seed():
    symbols = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j], dtype=complex) / np.sqrt(2)
    out1 = rayleigh_flat(symbols, snr_db=18, seed=2026)
    out2 = rayleigh_flat(symbols, snr_db=18, seed=2026)
    assert np.allclose(out1, out2)


def test_estimate_flat_channel_known_h():
    known = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j], dtype=complex) / np.sqrt(2)
    h = 0.7 - 0.35j
    received = h * known
    h_hat = estimate_flat_channel(received, known)
    assert abs(h_hat - h) < 1e-12


def test_cli_rayleigh_generates_metrics(tmp_path):
    test_file = PROJECT_ROOT / "Test.txt"
    test_file.write_text(
        "Rayleigh flat fading equalizer test with UTF-8 text: 无线通信提高模块。",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--input",
            "Test.txt",
            "--output",
            "results/received_rayleigh.txt",
            "--snr",
            "18",
            "--seed",
            "2026",
            "--mod",
            "qpsk",
            "--channel",
            "rayleigh",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    metrics = json.loads((PROJECT_ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["channel"] == "rayleigh"
    assert metrics["equalizer"] == "preamble_ls"
    assert metrics["channel_estimation"] is True
    assert "estimated_channel_real" in metrics
    assert "estimated_channel_imag" in metrics

