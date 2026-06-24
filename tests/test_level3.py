"""Level 3 extension tests: Rayleigh channel and convolutional code."""

import numpy as np

from src.channel import rayleigh
from src.conv_coding import conv_encode, viterbi_decode
from src.transmitter import run_transmitter
from src.receiver import run_receiver
from src.channel import awgn


def test_l3_rayleigh_runs_without_crash():
    text = "衰落信道测试"
    tx, meta = run_transmitter(text, seed=2026)
    rx, h = rayleigh(tx, snr_db=12, seed=2026)
    assert len(rx) == len(tx)
    assert len(h) == len(tx)


def test_l3_convolutional_noiseless_reversible():
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    coded = conv_encode(bits)
    decoded = viterbi_decode(coded)
    assert decoded == bits


def test_l3_awgn_vs_rayleigh_match_rate():
    text = "AWGN与Rayleigh对比"
    tx, meta = run_transmitter(text, seed=42)
    rx_awgn = awgn(tx, snr_db=10, seed=42)
    rx_ray, _ = rayleigh(tx, snr_db=10, seed=42)
    _, m_awgn = run_receiver(rx_awgn, seed=42, preamble_symbols=meta["preamble_symbols"], original_text=text)
    _, m_ray = run_receiver(rx_ray, seed=42, preamble_symbols=meta["preamble_symbols"], original_text=text)
    assert m_awgn["text_match_rate"] >= m_ray["text_match_rate"]
