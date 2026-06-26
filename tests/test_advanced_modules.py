import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from src.channel import awgn, rayleigh_mrc2
from src.convolutional import conv_encode, viterbi_decode
from src.modulation import (
    bits_per_symbol,
    demodulate_symbols,
    modulate_bits,
    select_adaptive_modulation,
)
from src.ofdm import ofdm_demodulate, ofdm_modulate
from src.pipeline import bit_error_rate, run_pipeline


def test_adaptive_modulation_thresholds_and_round_trips():
    assert select_adaptive_modulation(3) == "bpsk"
    assert select_adaptive_modulation(10) == "qpsk"
    assert select_adaptive_modulation(18) == "16qam"

    rng = np.random.default_rng(123)
    for scheme in ["bpsk", "qpsk", "16qam"]:
        nbits = 8 * bits_per_symbol(scheme)
        bits = [int(x) for x in rng.integers(0, 2, size=nbits)]
        symbols = modulate_bits(bits, scheme)
        recovered = demodulate_symbols(symbols, scheme)[: len(bits)]
        assert recovered == bits


def test_convolutional_code_viterbi_corrects_one_coded_bit_error():
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    coded = conv_encode(bits)
    corrupted = coded.copy()
    corrupted[5] ^= 1

    decoded = viterbi_decode(corrupted)[: len(bits)]

    assert decoded == bits


def test_ofdm_round_trip_preserves_symbols():
    bits = [0, 0, 0, 1, 1, 1, 1, 0] * 20
    symbols = modulate_bits(bits, "qpsk")

    samples, padded_count = ofdm_modulate(symbols, fft_size=16, cp_len=4)
    recovered = ofdm_demodulate(samples, symbol_count=len(symbols), fft_size=16, cp_len=4)

    assert padded_count >= len(symbols)
    assert np.allclose(recovered, symbols)


def test_mrc2_diversity_returns_equalized_symbols_and_no_worse_ber_than_single_branch():
    rng = np.random.default_rng(9)
    bits = [int(x) for x in rng.integers(0, 2, size=1200)]
    symbols = modulate_bits(bits, "qpsk")

    single = awgn(symbols, snr_db=7, seed=2027)
    single_bits = demodulate_symbols(single, "qpsk")[: len(bits)]
    combined, gains = rayleigh_mrc2(symbols, snr_db=7, seed=2027)
    combined_bits = demodulate_symbols(combined, "qpsk")[: len(bits)]

    assert combined.shape == symbols.shape
    assert len(gains) == 2
    assert bit_error_rate(bits, combined_bits) <= bit_error_rate(bits, single_bits)


def test_pipeline_runs_all_advanced_modules(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    input_path.write_text("Advanced OFDM diversity convolutional adaptive test.", encoding="utf-8")

    metrics = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        snr_db=24,
        seed=2026,
        modulation="adaptive",
        channel_name="rayleigh",
        coding_mode="conv",
        diversity="mrc2",
        ofdm_enabled=True,
    )

    assert output_path.read_text(encoding="utf-8") == input_path.read_text(encoding="utf-8")
    assert metrics["requested_modulation"] == "adaptive"
    assert metrics["effective_modulation"] == "16qam"
    assert metrics["channel_code"] == "convolutional-viterbi"
    assert metrics["ofdm_enabled"] is True
    assert metrics["diversity"] == "mrc2"
    assert metrics["checksum_pass"] is True


def test_cli_accepts_advanced_module_flags(tmp_path):
    input_path = tmp_path / "Test.txt"
    output_path = tmp_path / "results" / "received.txt"
    input_path.write_text("Advanced CLI flags test.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "main.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--snr",
            "24",
            "--seed",
            "2026",
            "--mod",
            "adaptive",
            "--channel",
            "rayleigh",
            "--coding",
            "conv",
            "--diversity",
            "mrc2",
            "--ofdm",
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert output_path.read_text(encoding="utf-8") == input_path.read_text(encoding="utf-8")
    assert metrics["effective_modulation"] == "16qam"
    assert metrics["ofdm_enabled"] is True
