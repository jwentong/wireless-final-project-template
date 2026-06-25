import numpy as np

H = np.array([[1, 1, 0, 1, 1, 0, 0],
              [1, 0, 1, 1, 0, 1, 0],
              [0, 1, 1, 1, 0, 0, 1]], dtype=int)

SYNDROME_TABLE = {
    (0, 0, 0): -1,
    (1, 1, 0): 0,
    (1, 0, 1): 1,
    (0, 1, 1): 2,
    (1, 1, 1): 3,
    (1, 0, 0): 4,
    (0, 1, 0): 5,
    (0, 0, 1): 6,
}


def channel_encode(bits: list[int]) -> list[int]:
    n = len(bits)
    if n % 4 != 0:
        bits = bits + [0] * (4 - n % 4)
    coded = []
    for i in range(0, len(bits), 4):
        m = np.array(bits[i:i + 4], dtype=int)
        p1 = m[0] ^ m[1] ^ m[3]
        p2 = m[0] ^ m[2] ^ m[3]
        p3 = m[1] ^ m[2] ^ m[3]
        coded.extend([m[0], m[1], m[2], m[3], p1, p2, p3])
    return coded


def channel_decode(bits: list[int]) -> list[int]:
    decoded_bits = []
    for i in range(0, len(bits), 7):
        if i + 7 > len(bits):
            break
        r = np.array(bits[i:i + 7], dtype=int)
        s = (H @ r) % 2
        syndrome = tuple(s.tolist())
        error_pos = SYNDROME_TABLE.get(syndrome, -1)
        if error_pos >= 0:
            r[error_pos] ^= 1
        decoded_bits.extend([int(r[0]), int(r[1]), int(r[2]), int(r[3])])
    return decoded_bits
