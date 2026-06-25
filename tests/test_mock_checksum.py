import numpy as np
from src.checksum import crc32_checksum, get_checksum_fn, get_checksum_len


class TestCRC32:

    def test_output_32_bits(self):
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        crc = crc32_checksum(bits)
        assert len(crc) == 32

    def test_deterministic(self):
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        assert crc32_checksum(bits) == crc32_checksum(bits)

    def test_different_inputs_differ(self):
        bits_a = [1, 0, 1, 1, 0, 0, 1, 0]
        bits_b = [1, 0, 1, 1, 0, 0, 1, 1]
        assert crc32_checksum(bits_a) != crc32_checksum(bits_b)

    def test_checksum_len(self):
        assert get_checksum_len("xor8") == 8
        assert get_checksum_len("crc32") == 32

    def test_get_checksum_fn_crc32(self):
        fn = get_checksum_fn("crc32")
        bits = [1, 1, 1, 1, 0, 0, 0, 0]
        result = fn(bits)
        assert len(result) == 32

    def test_get_checksum_fn_xor8(self):
        from src.framing import xor_checksum
        fn = get_checksum_fn("xor8")
        assert fn is xor_checksum

    def test_varying_input_lengths(self):
        rng = np.random.RandomState(42)
        for length in [1, 7, 8, 100, 1000]:
            bits = [int(rng.randint(0, 2)) for _ in range(length)]
            crc = crc32_checksum(bits)
            assert len(crc) == 32
