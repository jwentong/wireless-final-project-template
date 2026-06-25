from src.source import source_encode, source_decode


class TestSourceCodec:

    def test_utf8_encoding_reversible(self, sample_text):
        bits = source_encode(sample_text)
        recovered = source_decode(bits)
        assert recovered == sample_text

    def test_encoding_returns_bit_list(self, sample_text):
        bits = source_encode(sample_text)
        assert isinstance(bits, list)
        assert all(b in (0, 1) for b in bits)

    def test_empty_string(self):
        bits = source_encode("")
        assert len(bits) == 0
        recovered = source_decode(bits)
        assert recovered == ""

    def test_multibyte_characters(self):
        text = "你好世界🌍"
        bits = source_encode(text)
        recovered = source_decode(bits)
        assert recovered == text

    def test_decoding_strips_incomplete_bytes(self):
        bits = [1, 0, 1, 0, 1, 0, 1]  # 7 bits (not byte-aligned)
        recovered = source_decode(bits)
        assert isinstance(recovered, str)

    def test_preserves_bit_count(self, sample_text):
        bits = source_encode(sample_text)
        expected_bit_count = len(sample_text.encode("utf-8")) * 8
        assert len(bits) == expected_bit_count
