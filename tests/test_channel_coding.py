import numpy as np

from src.channel_coding import (
    channel_encode, channel_decode,
    conv_encode, viterbi_decode,
    hamming_encode, hamming_decode,
)


def test_conv_reversible_noiseless():
    bits = np.random.default_rng(2).integers(0, 2, 400).tolist()
    assert channel_decode(channel_encode(bits))[:400] == bits


def test_conv_rate_one_half():
    bits = [1, 0, 1, 1, 0, 0]
    # output length = 2 * (N + K-1) = 2 * (6 + 6) = 24
    assert len(conv_encode(bits)) == 2 * (len(bits) + 6)


def test_conv_corrects_sparse_errors():
    bits = np.random.default_rng(3).integers(0, 2, 200).tolist()
    coded = conv_encode(bits)
    coded[10] ^= 1
    coded[57] ^= 1
    coded[123] ^= 1
    assert viterbi_decode(coded)[:200] == bits


def test_hamming_reversible_noiseless():
    bits = np.random.default_rng(4).integers(0, 2, 400).tolist()
    assert hamming_decode(hamming_encode(bits))[:400] == bits


def test_hamming_corrects_single_error_per_block():
    bits = [1, 0, 1, 1]
    coded = hamming_encode(bits)
    coded[2] ^= 1  # flip one bit
    assert hamming_decode(coded)[:4] == bits


def test_channel_encode_hamming_scheme():
    bits = np.random.default_rng(5).integers(0, 2, 40).tolist()
    coded = channel_encode(bits, scheme="hamming")
    assert channel_decode(coded, scheme="hamming")[:40] == bits
