import json
import subprocess
import sys
import uuid
from pathlib import Path

from src.convolutional import convolutional_encode, viterbi_decode


def test_unified_cli_smoke():
    root = Path(__file__).resolve().parents[1]
    tmp_path = root / "work" / f"smoke_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=True)
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    text = "无线通信隐藏场景 smoke test: QPSK, AWGN, sync, coding."
    input_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--snr",
            "12",
            "--seed",
            "2026",
            "--mod",
            "qpsk",
            "--channel",
            "awgn",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == text
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["checksum_pass"] is True
    assert metrics["text_match_rate"] == 1.0


def test_level3_convolutional_viterbi_round_trip():
    bits = [int((i * 7 + 3) % 2) for i in range(127)]
    encoded = convolutional_encode(bits)
    decoded = viterbi_decode(encoded)
    assert decoded == bits


def test_level3_rayleigh_cli_smoke():
    root = Path(__file__).resolve().parents[1]
    tmp_path = root / "work" / f"rayleigh_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=True)
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received_rayleigh.txt"
    input_path.write_text("Rayleigh ZF equalization level 3 smoke.", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--snr",
            "18",
            "--seed",
            "2026",
            "--mod",
            "qpsk",
            "--channel",
            "rayleigh",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["channel"] == "rayleigh"
    assert metrics["equalizer"] == "ZF"
    assert "rayleigh_flat_fading" in metrics["level3_modules"]
