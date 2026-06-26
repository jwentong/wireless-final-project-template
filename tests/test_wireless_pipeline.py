import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from src.channel import awgn, equalize_flat_rayleigh, rayleigh_flat
from src.framing import build_frame, parse_frame
from src.modulation import qpsk_demodulate, qpsk_modulate
from src.pipeline import run_pipeline
from src.source import source_decode, source_encode
from src.synchronization import detect_frame_start


def test_utf8_source_codec_round_trips_chinese_text():
    text = "无线通信 QPSK 链路测试：同步、编码、解码。"
    bits = source_encode(text)

    assert len(bits) % 8 == 0
    assert source_decode(bits) == text


def test_frame_round_trip_preserves_odd_length_payload():
    payload = [int(x) for x in np.random.default_rng(7).integers(0, 2, size=257)]
    frame = build_frame(payload)
    parsed = parse_frame(frame["bits"])

    assert parsed["length"] == 257
    assert parsed["payload"] == payload
    assert parsed["checksum_pass"] is True


def test_qpsk_uses_required_gray_mapping_and_demaps_without_noise():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
    expected = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)

    assert np.allclose(symbols[:4], expected)
    assert qpsk_demodulate(symbols)[:8] == [0, 0, 0, 1, 1, 1, 1, 0]


def test_awgn_is_seed_reproducible():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])

    assert np.allclose(awgn(symbols, snr_db=12, seed=2026), awgn(symbols, snr_db=12, seed=2026))


def test_rayleigh_flat_channel_can_be_equalized_with_known_gain():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0] * 8)

    faded, gain = rayleigh_flat(symbols, snr_db=40, seed=2026, return_gain=True)
    equalized = equalize_flat_rayleigh(faded, gain)

    assert qpsk_demodulate(equalized)[: len(symbols) * 2] == qpsk_demodulate(symbols)


def test_detect_frame_start_handles_symbol_offset():
    preamble = qpsk_modulate(build_frame([])["preamble"])
    prefix = np.zeros(37, dtype=complex)
    received = np.concatenate([prefix, preamble, np.ones(20, dtype=complex)])

    result = detect_frame_start(received, preamble=preamble)

    assert abs(result["start_index"] - 37) <= 1


def test_pipeline_recovers_text_at_12db(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    input_path.write_text("端到端无线通信基带仿真测试。", encoding="utf-8")

    metrics = run_pipeline(input_path, output_path, snr_db=12, seed=2026, modulation="qpsk", channel_name="awgn")

    assert output_path.read_text(encoding="utf-8") == input_path.read_text(encoding="utf-8")
    assert metrics["text_match_rate"] == 1.0
    assert metrics["checksum_pass"] is True


def test_pipeline_frame_length_and_crc_use_original_payload_bits(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    input_path.write_text("PRD length CRC semantics test.", encoding="utf-8")

    metrics = run_pipeline(input_path, output_path, snr_db=12, seed=2026, modulation="qpsk", channel_name="awgn")

    assert metrics["frame_payload_bits"] == metrics["payload_bits"]
    assert metrics["frame_crc_scope"] == "original-payload-bits"
    assert metrics["frame_crc_pass"] is True


def test_cli_generates_metrics_and_received_text(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    input_path.write_text("CLI 统一入口测试。", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "main.py"),
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
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert output_path.read_text(encoding="utf-8") == input_path.read_text(encoding="utf-8")
    assert metrics["modulation"] == "qpsk"


def test_cli_supports_rayleigh_extension_with_equalization(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    input_path.write_text("Rayleigh 提高模块测试。", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "main.py"),
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
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert output_path.read_text(encoding="utf-8") == input_path.read_text(encoding="utf-8")
    assert metrics["channel"] == "rayleigh"
    assert metrics["equalizer"] == "perfect-csi-one-tap"
