import json
from pathlib import Path

import numpy as np

from main import run_chain
from src.channel import awgn
from src.framing import PREAMBLE_BITS
from src.modulation import qpsk_modulate
from src.synchronization import synchronize


def test_convolutional_chain_recovers_different_utf8_text(tmp_path):
    text = "深圳大学无线通信期末项目：QPSK、AWGN、同步、卷积码和 Viterbi。"
    input_path = tmp_path / "case.txt"
    output_path = tmp_path / "received.txt"
    input_path.write_text(text, encoding="utf-8")

    metrics = run_chain(input_path, output_path, snr_db=12, seed=4096, modulation="qpsk", channel_name="awgn")

    assert output_path.read_text(encoding="utf-8") == text
    assert metrics["ber"] == 0.0
    assert metrics["checksum_pass"] is True


def test_preamble_sync_handles_random_offsets():
    rng = np.random.default_rng(2024080709)
    preamble = qpsk_modulate(PREAMBLE_BITS)
    payload = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0] * 20)
    for offset in [0, 1, 25, 64, 128]:
        prefix = (rng.normal(size=offset) + 1j * rng.normal(size=offset)) / np.sqrt(2)
        received = awgn(np.concatenate([prefix, preamble, payload]), snr_db=12, seed=offset + 7)
        sync_info = synchronize(received, preamble=preamble)
        assert abs(int(sync_info["start_index"]) - offset) <= 1


def test_low_snr_still_writes_metrics(tmp_path):
    input_path = tmp_path / "case.txt"
    output_path = tmp_path / "received.txt"
    input_path.write_text("低信噪比测试：系统可以失败，但不能崩溃。", encoding="utf-8")

    metrics = run_chain(input_path, output_path, snr_db=0, seed=2026, modulation="qpsk", channel_name="awgn")
    metrics_path = output_path.parent / "metrics.json"

    assert output_path.exists()
    assert metrics_path.exists()
    loaded = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "ber" in loaded
    assert "text_match_rate" in loaded
    assert metrics["snr_db"] == 0.0

