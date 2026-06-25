"""Channel coding module — Hamming(7,4) code."""

import numpy as np


# Hamming(7,4) generator matrix (systematic form)
# G = [I4 | P]
# Parity submatrix P
_P = np.array(
    [
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 1],
    ],
    dtype=int,
)

# Parity-check matrix H = [P^T | I3]
_H = np.concatenate([_P.T, np.eye(3, dtype=int)], axis=1)

# Syndrome lookup table: syndrome (as integer) -> error bit position (0-based)
# syndrome = H · r^T  (mod 2), where r is the received 7-bit codeword
_SYNDROME_TO_POS = {}
for error_pos in range(7):
    error_vec = np.zeros(7, dtype=int)
    error_vec[error_pos] = 1
    syndrome = (_H @ error_vec) % 2
    syndrome_key = tuple(syndrome.tolist())
    _SYNDROME_TO_POS[syndrome_key] = error_pos
# Syndrome (0,0,0) means no error


def channel_encode(bits: list[int]) -> list[int]:
    """Encode bits using Hamming(7,4).

    Groups input bits into blocks of 4, encodes each block into 7 bits.
    If the last block has fewer than 4 bits, pads with zeros.

    Args:
        bits: List of input bits.

    Returns:
        Encoded bits (length = ceil(len(bits)/4) * 7).
    """
    # Pad to multiple of 4
    original_len = len(bits)
    padded = list(bits)
    while len(padded) % 4 != 0:
        padded.append(0)

    encoded = []
    for i in range(0, len(padded), 4):
        data = np.array(padded[i : i + 4], dtype=int)
        # Systematic: first 4 bits = data, last 3 bits = parity = data @ P (mod 2)
        parity = (data @ _P) % 2
        codeword = np.concatenate([data, parity])
        encoded.extend(codeword.tolist())

    return encoded


def channel_decode(bits: list[int]) -> list[int]:
    """Decode Hamming(7,4) encoded bits with single-error correction.

    Args:
        bits: Encoded bits (length should be multiple of 7).

    Returns:
        Decoded bits. Extra padding from encoding is removed.
    """
    if len(bits) % 7 != 0:
        # Pad to multiple of 7 if needed
        bits = list(bits)
        while len(bits) % 7 != 0:
            bits.append(0)

    decoded = []
    for i in range(0, len(bits), 7):
        codeword = np.array(bits[i : i + 7], dtype=int)
        # Compute syndrome
        syndrome = tuple(((_H @ codeword) % 2).tolist())
        if syndrome in _SYNDROME_TO_POS:
            error_pos = _SYNDROME_TO_POS[syndrome]
            codeword[error_pos] ^= 1  # flip the erroneous bit
        # else: syndrome is (0,0,0) → no error, or uncorrectable → pass through
        # Extract data bits (first 4)
        decoded.extend(codeword[:4].tolist())

    return decoded


# Aliases for test discovery
encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode
