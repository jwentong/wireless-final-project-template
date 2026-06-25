import numpy as np

G1 = 0o133
G2 = 0o171
K = 7
NUM_STATES = 1 << (K - 1)


def _popcount(x: int) -> int:
    return bin(x).count("1")


_NEXT_STATE = [[0, 0] for _ in range(NUM_STATES)]
_EXPECTED_OUT = [[0, 0] for _ in range(NUM_STATES)]

for s in range(NUM_STATES):
    for b in [0, 1]:
        combined = (b << (K - 1)) | s
        out0 = _popcount(combined & G1) & 1
        out1 = _popcount(combined & G2) & 1
        out = (out0 << 1) | out1
        ns = (s >> 1) | (b << (K - 2))
        if b == 0:
            _NEXT_STATE[s][0] = ns
            _EXPECTED_OUT[s][0] = out
        else:
            _NEXT_STATE[s][1] = ns
            _EXPECTED_OUT[s][1] = out

_PRED_STATES = [[0, 0] for _ in range(NUM_STATES)]
_EXPECTED_BITS = [[0, 0] for _ in range(NUM_STATES)]

for t in range(NUM_STATES):
    b = (t >> (K - 2)) & 1
    for wp in [0, 1]:
        s = ((t << 1) & (NUM_STATES - 1)) | wp
        combined = (b << (K - 1)) | s
        out0 = _popcount(combined & G1) & 1
        out1 = _popcount(combined & G2) & 1
        _PRED_STATES[t][wp] = s
        _EXPECTED_BITS[t][wp] = (out0 << 1) | out1


def conv_encode(bits: list[int]) -> list[int]:
    bits = list(bits) + [0] * (K - 1)
    output = []
    reg = 0
    for bit in bits:
        state = reg
        b = bit
        ns = (state >> 1) | (b << (K - 2))
        out = _EXPECTED_OUT[state][b]
        output.append((out >> 1) & 1)
        output.append(out & 1)
        reg = ns
    return output


def viterbi_decode(bits: list[int]) -> list[int]:
    num_steps = len(bits) // 2
    path_metrics = np.full(NUM_STATES, 1e9, dtype=np.float64)
    path_metrics[0] = 0.0
    tb = np.zeros((num_steps, NUM_STATES), dtype=np.int32)

    for step in range(num_steps):
        r0 = bits[2 * step]
        r1 = bits[2 * step + 1]
        r = (r0 << 1) | r1
        new_pm = np.full(NUM_STATES, 1e9, dtype=np.float64)

        for t in range(NUM_STATES):
            for wp in [0, 1]:
                s = _PRED_STATES[t][wp]
                expected = _EXPECTED_BITS[t][wp]
                bm = _popcount(r ^ expected)
                cand = path_metrics[s] + bm
                if cand < new_pm[t]:
                    new_pm[t] = cand
                    tb[step, t] = s

        path_metrics = new_pm

    best = int(np.argmin(path_metrics))
    decoded = []
    state = best
    for step in range(num_steps - 1, -1, -1):
        b = (state >> (K - 2)) & 1
        decoded.append(b)
        state = tb[step, state]

    decoded.reverse()
    return decoded[:-(K - 1)]


def hamming_encode(bits: list[int]) -> list[int]:
    n = len(bits)
    if n % 4 != 0:
        bits = bits + [0] * (4 - n % 4)
    coded = []
    for i in range(0, len(bits), 4):
        m = bits[i:i + 4]
        p1 = m[0] ^ m[1] ^ m[3]
        p2 = m[0] ^ m[2] ^ m[3]
        p3 = m[1] ^ m[2] ^ m[3]
        coded.extend([m[0], m[1], m[2], m[3], p1, p2, p3])
    return coded


def hamming_decode(bits: list[int]) -> list[int]:
    H = np.array([[1, 1, 0, 1, 1, 0, 0],
                  [1, 0, 1, 1, 0, 1, 0],
                  [0, 1, 1, 1, 0, 0, 1]], dtype=int)
    SYNDROME_TABLE = {
        (0, 0, 0): -1, (1, 1, 0): 0, (1, 0, 1): 1, (0, 1, 1): 2,
        (1, 1, 1): 3, (1, 0, 0): 4, (0, 1, 0): 5, (0, 0, 1): 6,
    }
    decoded = []
    for i in range(0, len(bits), 7):
        if i + 7 > len(bits):
            break
        r = np.array(bits[i:i + 7], dtype=int)
        s = tuple(((H @ r) % 2).tolist())
        ep = SYNDROME_TABLE.get(s, -1)
        if ep >= 0:
            r[ep] ^= 1
        decoded.extend([int(r[0]), int(r[1]), int(r[2]), int(r[3])])
    return decoded


FEC_SCHEMES = {
    "hamming": {"encode": hamming_encode, "decode": hamming_decode},
    "convolutional": {"encode": conv_encode, "decode": viterbi_decode},
}


def get_fec(name: str) -> dict:
    return FEC_SCHEMES.get(name, FEC_SCHEMES["hamming"])
