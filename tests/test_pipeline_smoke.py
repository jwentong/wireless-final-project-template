from pathlib import Path

from src.pipeline import run_transmission


def test_pipeline_smoke(tmp_path: Path):
    src = tmp_path / "Test.txt"
    dst = tmp_path / "results" / "received.txt"
    text = "无线通信 QPSK AWGN 同步测试"
    src.write_text(text, encoding="utf-8")
    metrics = run_transmission(src, dst, snr_db=12, seed=2026)
    assert dst.read_text(encoding="utf-8") == text
    assert metrics["text_match_rate"] == 1.0
    assert metrics["checksum_pass"] is True

