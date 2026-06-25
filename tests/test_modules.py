import numpy as np
from src.source import source_encode, source_decode
from src.crypto import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame, PREAMBLE_BITS
from src.modulation import qpsk_modulate, qpsk_demodulate, bpsk_modulate, bpsk_demodulate, qam16_modulate, qam16_demodulate
from src.channel import awgn, rayleigh
from src.synchronization import synchronize, compute_sync_metric
from src.ofdm import ofdm_modulate, ofdm_demodulate
from src.diversity import maximal_ratio_combine, selection_combine, equal_gain_combine
from src.adaptive import select_modulation, get_bits_per_symbol

SAMPLE_TEXT = "无线通信技术课程要求学生理解调制、编码、信道和接收机处理。"


def test_source_encode_decode():
    bits = source_encode(SAMPLE_TEXT)
    assert len(bits) % 8 == 0
    recovered = source_decode(bits)
    assert recovered == SAMPLE_TEXT


def test_scramble_reversible():
    bits = [int(x) for x in np.random.default_rng(2026).integers(0, 2, size=511)]
    scrambled = scramble(bits, seed=2026)
    descrambled = descramble(scrambled, seed=2026)
    assert descrambled == bits


def test_channel_coding_reversible():
    bits = [int(x) for x in np.random.default_rng(2028).integers(0, 2, size=400)]
    coded = channel_encode(bits, method="hamming")
    decoded = channel_decode(coded, method="hamming")
    assert decoded[:len(bits)] == bits


def test_frame_build_parse():
    payload = [int(x) for x in np.random.default_rng(2027).integers(0, 2, size=257)]
    frame = build_frame(payload)
    parsed = parse_frame(frame)
    assert parsed["payload"][:len(payload)] == payload
    assert parsed["length"] == len(payload)


def test_qpsk_modem():
    bits = [int(x) for x in np.random.default_rng(2029).integers(0, 2, size=512)]
    symbols = qpsk_modulate(bits)
    recovered = qpsk_demodulate(symbols)
    assert recovered[:len(bits)] == bits


def test_bpsk_modem():
    bits = [int(x) for x in np.random.default_rng(0).integers(0, 2, size=100)]
    symbols = bpsk_modulate(bits)
    recovered = bpsk_demodulate(symbols)
    assert recovered == bits


def test_qam16_modem():
    bits = [int(x) for x in np.random.default_rng(1).integers(0, 2, size=400)]
    symbols = qam16_modulate(bits)
    recovered = qam16_demodulate(symbols)
    assert recovered[:len(bits)] == bits


def test_awgn_reproducible():
    symbols = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j], dtype=complex) / np.sqrt(2)
    out1 = awgn(symbols, snr_db=12, seed=2026)
    out2 = awgn(symbols, snr_db=12, seed=2026)
    assert np.allclose(out1, out2)


def test_sync_detection():
    rng = np.random.default_rng(2026)
    preamble_symbols = np.array(qpsk_modulate(PREAMBLE_BITS), dtype=complex)
    payload = np.array([1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 20, dtype=complex) / np.sqrt(2)
    prefix = (rng.normal(size=25) + 1j * rng.normal(size=25)) / np.sqrt(2)
    received = np.concatenate([prefix, preamble_symbols, payload])
    start = synchronize(received, preamble_symbols)
    assert abs(int(start) - 25) <= 1


def test_rayleigh_channel():
    symbols = np.array([1 + 1j, -1 + 1j], dtype=complex) / np.sqrt(2)
    out = rayleigh(symbols, snr_db=20, seed=2026)
    assert len(out) == len(symbols)
    assert np.any(out != symbols)


def test_ofdm():
    symbols = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 4, dtype=complex) / np.sqrt(2)
    tx = ofdm_modulate(symbols)
    rx = ofdm_demodulate(tx)
    assert len(rx) >= len(symbols)
    assert np.allclose(rx[:len(symbols)], symbols, atol=1e-10)


def test_diversity():
    rng = np.random.default_rng(2026)
    n_rx = 3
    n_sym = 10
    rx_signals = rng.normal(size=(n_rx, n_sym)) + 1j * rng.normal(size=(n_rx, n_sym))
    ch_est = rng.normal(size=(n_rx, n_sym)) + 1j * rng.normal(size=(n_rx, n_sym))
    combined = maximal_ratio_combine(rx_signals, ch_est)
    assert len(combined) == n_sym
    sel = selection_combine(rx_signals, ch_est)
    assert len(sel) == n_sym
    egc = equal_gain_combine(rx_signals)
    assert len(egc) == n_sym


def test_adaptive_modulation():
    assert select_modulation(5) == "bpsk"
    assert select_modulation(10) == "qpsk"
    assert select_modulation(20) == "16qam"
    assert get_bits_per_symbol("bpsk") == 1
    assert get_bits_per_symbol("qpsk") == 2
    assert get_bits_per_symbol("16qam") == 4
