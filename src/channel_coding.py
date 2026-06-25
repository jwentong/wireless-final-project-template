import numpy as np

def _hamming_74_encode(bits):
    result = []
    for i in range(0, len(bits) - len(bits) % 4, 4):
        d = bits[i:i + 4]
        p1 = d[0] ^ d[1] ^ d[3]
        p2 = d[0] ^ d[2] ^ d[3]
        p3 = d[1] ^ d[2] ^ d[3]
        result.extend([d[0], d[1], d[2], d[3], p1, p2, p3])
    remaining = len(bits) % 4
    if remaining > 0:
        for b in bits[-remaining:]:
            result.append(b)
    return result

def _hamming_74_decode(bits):
    result = []
    for i in range(0, len(bits) - len(bits) % 7, 7):
        r = bits[i:i + 7]
        s1 = r[0] ^ r[1] ^ r[3] ^ r[4]
        s2 = r[0] ^ r[2] ^ r[3] ^ r[5]
        s3 = r[1] ^ r[2] ^ r[3] ^ r[6]
        syndrome = (s3 << 2) | (s2 << 1) | s1
        error_pos = {1: 4, 2: 5, 3: 0, 4: 6, 5: 1, 6: 2, 7: 3}
        if syndrome in error_pos:
            pos = error_pos[syndrome]
            r = list(r)
            r[pos] ^= 1
        result.extend(r[:4])
    remaining = len(bits) % 7
    if remaining > 0:
        for b in bits[-remaining:]:
            result.append(b)
    return result

_CONV_GENERATORS = (0o7, 0o5)
_CONV_CONSTRAINT = 3
_CONV_CODE_RATE = 2

def _conv_encode(bits):
    reg = [0] * (_CONV_CONSTRAINT - 1)
    output = []
    for b in bits:
        reg.insert(0, b)
        reg.pop()
        g1 = reg[0] ^ reg[1] ^ reg[2]
        g2 = reg[0] ^ reg[2]
        output.extend([g1, g2])
    return output

def _viterbi_decode(bits, tb_depth=14):
    bits = list(bits)
    if len(bits) < 2:
        return bits[:]
    num_states = 1 << (_CONV_CONSTRAINT - 1)
    inf = float("inf")
    path_metric = [0.0] + [inf] * (num_states - 1)
    traceback = []

    def next_state(state, bit):
        return (bit << (_CONV_CONSTRAINT - 2)) | (state >> 1)

    def expected_output(state, bit):
        g1 = (bit ^ (state >> 1) ^ state) & 1
        g2 = (bit ^ state) & 1
        return [g1, g2]

    for i in range(0, len(bits) - 1, 2):
        if i + 1 >= len(bits):
            break
        recv = [bits[i], bits[i + 1]]
        new_metric = [inf] * num_states
        new_tb = [0] * num_states
        for state in range(num_states):
            if path_metric[state] == inf:
                continue
            for inp in (0, 1):
                ns = next_state(state, inp)
                exp = expected_output(state, inp)
                dist = sum(r ^ e for r, e in zip(recv, exp))
                pm = path_metric[state] + dist
                if pm < new_metric[ns]:
                    new_metric[ns] = pm
                    new_tb[ns] = (state << 1) | inp
        path_metric = new_metric
        traceback.append(new_tb)

    if not traceback:
        return bits[:]

    best_state = min(range(num_states), key=lambda s: path_metric[s])
    decoded = []
    for tb in reversed(traceback):
        inp = best_state & 1
        decoded.insert(0, inp)
        best_state = (tb[best_state] >> 1) & (num_states - 1)

    return decoded

def channel_encode(bits, method="hamming"):
    if method == "none":
        return list(bits)
    if method == "hamming":
        return _hamming_74_encode(bits)
    if method == "convolutional":
        return _conv_encode(bits)
    return _hamming_74_encode(bits)

def channel_decode(bits, method="hamming"):
    if method == "none":
        return list(bits)
    if method == "hamming":
        return _hamming_74_decode(bits)
    if method == "convolutional":
        return _viterbi_decode(bits)
    return _hamming_74_decode(bits)

def encode(bits, method="hamming"):
    return channel_encode(bits, method)

def decode(bits, method="hamming"):
    return channel_decode(bits, method)

def encode_bits(bits, method="hamming"):
    return channel_encode(bits, method)

def decode_bits(bits, method="hamming"):
    return channel_decode(bits, method)

def fec_encode(bits, method="hamming"):
    return channel_encode(bits, method)

def fec_decode(bits, method="hamming"):
    return channel_decode(bits, method)
