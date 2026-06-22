import json
import subprocess
import sys
from pathlib import Path


def test_cli_end_to_end_recovers_temp_text(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "out" / "received.txt"
    text = "临时中文文本 QPSK AWGN 同步测试。\n第二行用于验证换行。"
    input_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "main.py"),
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
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == text
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["text_match_rate"] == 1.0
    assert metrics["checksum_pass"] is True


def test_cli_rayleigh_extension_recovers_temp_text(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "input_rayleigh.txt"
    output_path = tmp_path / "rayleigh" / "received.txt"
    text = "Rayleigh 扩展信道测试，包含中文和 punctuation."
    input_path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "main.py"),
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
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == text
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["channel"] == "rayleigh"
    assert metrics["text_match_rate"] == 1.0
    assert metrics["checksum_pass"] is True