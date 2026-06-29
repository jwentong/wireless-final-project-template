import numpy as np

from src.framing import build_frame, parse_frame, PREAMBLE_LEN


def test_frame_longer_than_payload():
    payload = np.random.default_rng(6).integers(0, 2, 2400).tolist()
    assert len(build_frame(payload)) > len(payload)


def test_roundtrip():
    payload = np.random.default_rng(7).integers(0, 2, 257).tolist()
    parsed = parse_frame(build_frame(payload))
    assert parsed["payload"][:257] == payload
    assert parsed["length"] == 257
    assert parsed["crc_pass"]


def test_orig_len_distinct_from_coded_len():
    payload = [1, 0, 1, 1, 0, 0, 1, 0]
    parsed = parse_frame(build_frame(payload, orig_len=5))
    assert parsed["length"] == 5
    assert parsed["coded_len"] == 8
    assert parsed["payload"][:8] == payload


def test_crc_detects_payload_corruption():
    payload = np.random.default_rng(8).integers(0, 2, 100).tolist()
    frame = build_frame(payload)
    frame[PREAMBLE_LEN + 192 + 10] ^= 1  # flip a payload bit
    assert not parse_frame(frame)["crc_pass"]


def test_frame_even_length():
    payload = np.random.default_rng(9).integers(0, 2, 255).tolist()
    assert len(build_frame(payload)) % 2 == 0


def test_header_survives_single_bit_error():
    # one bit flip inside the protected length header must be corrected
    payload = np.random.default_rng(10).integers(0, 2, 120).tolist()
    frame = build_frame(payload)
    frame[PREAMBLE_LEN + 1] ^= 1  # corrupt one header repetition bit
    parsed = parse_frame(frame)
    assert parsed["length"] == 120 and parsed["coded_len"] == 120
