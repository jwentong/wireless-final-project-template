import numpy as np
from src.fec import (
    conv_encode, viterbi_decode,
    hamming_encode, hamming_decode,
    get_fec,
)


class TestConvCodec:

    def test_conv_encode_decode_noiseless(self):
        bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
        encoded = conv_encode(bits)
        decoded = viterbi_decode(encoded)
        assert decoded == bits

    def test_varying_input_lengths(self):
        rng = np.random.RandomState(42)
        for length in [1, 7, 8, 15, 16, 100, 255, 512]:
            bits = [int(rng.randint(0, 2)) for _ in range(length)]
            encoded = conv_encode(bits)
            decoded = viterbi_decode(encoded)
            assert decoded == bits, f"Failed at length {length}"

    def test_single_bit_error_correction(self):
        bits = [1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1]
        encoded = conv_encode(bits)
        received = list(encoded)
        received[5] ^= 1
        decoded = viterbi_decode(received)
        assert decoded == bits

    def test_fec_factory_selects_hamming(self):
        scheme = get_fec("hamming")
        bits = [1, 0, 1, 1, 0]
        encoded = scheme["encode"](bits)
        decoded = scheme["decode"](encoded)
        assert decoded[:len(bits)] == bits

    def test_fec_factory_selects_convolutional(self):
        scheme = get_fec("convolutional")
        bits = [1, 0, 1, 1, 0, 1, 0, 0]
        encoded = scheme["encode"](bits)
        decoded = scheme["decode"](encoded)
        assert decoded == bits

    def test_fec_factory_default_hamming(self):
        scheme = get_fec("invalid")
        assert scheme is get_fec("hamming")

    def test_hamming_still_works(self):
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        encoded = hamming_encode(bits)
        decoded = hamming_decode(encoded)
        assert decoded[:len(bits)] == bits
