from src.framing import build_frame, parse_frame, PREAMBLE_BITS


class TestFrameStructure:

    def test_frame_contains_required_fields(self, test_payload):
        frame = build_frame(test_payload)
        preamble = frame[:32]
        length_bits = frame[32:48]
        payload_bits = frame[48:48 + len(test_payload)]
        checksum_bits = frame[48 + len(test_payload):48 + len(test_payload) + 8]
        assert preamble == PREAMBLE_BITS
        assert len(length_bits) == 16
        assert payload_bits == test_payload
        assert len(checksum_bits) == 8

    def test_frame_is_parsable(self, test_payload):
        frame = build_frame(test_payload)
        recovered, meta = parse_frame(frame)
        assert recovered == test_payload

    def test_checksum_passes_on_noiseless_frame(self, test_payload):
        frame = build_frame(test_payload)
        _, meta = parse_frame(frame)
        assert meta.get("checksum_pass") is True

    def test_length_field_matches_payload_size(self, test_payload):
        frame = build_frame(test_payload)
        _, meta = parse_frame(frame)
        assert meta["length"] == len(test_payload)

    def test_padding_for_odd_bit_count(self):
        payload = [1, 0, 1]  # 3 bits, odd
        frame = build_frame(payload)
        assert len(frame) % 2 == 0  # total must be even for QPSK
        recovered, meta = parse_frame(frame)
        assert recovered == payload

    def test_minimal_payload(self):
        payload = [1]
        frame = build_frame(payload)
        assert len(frame) % 2 == 0
        recovered, meta = parse_frame(frame)
        assert recovered == payload

    def test_large_payload(self):
        payload = [i % 2 for i in range(1000)]
        frame = build_frame(payload)
        recovered, meta = parse_frame(frame)
        assert recovered == payload

    def test_preamble_constant_unchanged(self):
        assert len(PREAMBLE_BITS) == 32
        assert all(b in (0, 1) for b in PREAMBLE_BITS)
