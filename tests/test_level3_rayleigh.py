import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from src.channel import one_tap_equalize, rayleigh_fading_channel
from src.modulation import qpsk_demodulate, qpsk_modulate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_rayleigh_channel_reproducibility():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0] * 16)
    rx1, h1 = rayleigh_fading_channel(symbols, snr_db=12, seed=2026)
    rx2, h2 = rayleigh_fading_channel(symbols, snr_db=12, seed=2026)
    assert np.allclose(rx1, rx2)
    assert np.allclose(h1, h2)


def test_one_tap_equalization_sanity_without_noise():
    bits = [0, 0, 0, 1, 1, 1, 1, 0] * 8
    symbols = qpsk_modulate(bits)
    h = np.array([1 + 0.5j, -0.75 + 0.8j, 0.4 - 1.2j, -1 - 0.2j] * 8)
    equalized = one_tap_equalize(h * symbols, h)
    recovered = qpsk_demodulate(equalized)[: len(bits)]
    assert recovered == bits


def test_cli_rayleigh_smoke():
    smoke_dir = PROJECT_ROOT / ".test_outputs"
    smoke_dir.mkdir(exist_ok=True)
    output_path = smoke_dir / "received_rayleigh_smoke.txt"
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--input",
            "Test.txt",
            "--output",
            str(output_path),
            "--snr",
            "12",
            "--seed",
            "2026",
            "--mod",
            "qpsk",
            "--channel",
            "rayleigh",
            "--no-plots",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    metrics = json.loads((smoke_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["channel"] == "rayleigh"
    assert metrics["equalization"] == "one-tap"
    assert metrics["fading_model"] == "flat_rayleigh"
    assert output_path.exists()
