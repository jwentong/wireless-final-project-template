import numpy as np

from src.channel import add_prefix, awgn
from src.channel_codec import repetition_decode, repetition_encode
from src.frame import build_frame, crc32_from_payload_bits, parse_frame
from src.modulation import qpsk_demodulate, qpsk_modulate
from src.scrambler import scramble_bits
from src.source_codec import source_decode, source_encode
from src.synchronization import detect_frame_start, preamble_symbols


def test_source_encode_decode_round_trip():
    text = "Hello QPSK. 无线通信 2026."
    bits = source_encode(text)
    assert len(bits) == len(text.encode("utf-8")) * 8
    assert source_decode(bits) == text


def test_scrambler_reversibility():
    bits = [int(x) for x in np.random.default_rng(1).integers(0, 2, size=257)]
    scrambled = scramble_bits(bits, seed=2026)
    recovered = scramble_bits(scrambled, seed=2026)
    assert recovered == bits


def test_repetition3_encode_decode():
    bits = [1, 0, 1, 0]
    encoded = repetition_encode(bits)
    assert encoded == [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0]
    assert repetition_decode([1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0]) == [1, 1, 0, 0]


def test_frame_build_parse():
    payload_bits = source_encode("frame check")
    scrambled = scramble_bits(payload_bits, seed=7)
    encoded_payload = repetition_encode(scrambled)
    frame_bits = build_frame(
        encoded_payload,
        payload_bit_length=len(payload_bits),
        checksum=crc32_from_payload_bits(payload_bits),
    )
    parsed = parse_frame(frame_bits)
    assert parsed["length"] == len(payload_bits)
    assert parsed["payload"] == encoded_payload
    assert parsed["checksum"] == crc32_from_payload_bits(payload_bits)


def test_qpsk_mapping_demapping_without_noise():
    bits = [0, 0, 0, 1, 1, 1, 1, 0]
    symbols = qpsk_modulate(bits)
    expected = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    assert np.allclose(symbols, expected)
    assert qpsk_demodulate(symbols) == bits


def test_awgn_fixed_seed_reproducibility():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0] * 10)
    rx1 = awgn(symbols, snr_db=12, seed=2026)
    rx2 = awgn(symbols, snr_db=12, seed=2026)
    assert np.allclose(rx1, rx2)


def test_synchronization_with_known_prefix_offset():
    preamble = preamble_symbols()
    payload = qpsk_modulate([1, 0, 0, 1, 1, 1, 0, 0] * 8)
    offset = 25
    received = add_prefix(np.concatenate([preamble, payload]), offset_symbols=offset, seed=11)
    result = detect_frame_start(received, preamble=preamble)
    assert result["start_index"] == offset
