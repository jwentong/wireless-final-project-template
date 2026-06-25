def _parity(value):
    return int(value.bit_count() & 1)


def _next_state_and_output(state, bit):
    """Constraint length 3 convolutional code with generators 111 and 101."""
    bit = int(bit)
    reg = (bit << 2) | int(state)
    out0 = _parity(reg & 0b111)
    out1 = _parity(reg & 0b101)
    next_state = reg >> 1
    return next_state, (out0, out1)


def convolutional_encode(bits, terminate=True):
    state = 0
    encoded = []
    input_bits = [int(bit) for bit in bits]
    if terminate:
        input_bits = input_bits + [0, 0]
    for bit in input_bits:
        state, pair = _next_state_and_output(state, bit)
        encoded.extend(pair)
    return encoded


def viterbi_decode(bits, terminate=True):
    coded = [int(bit) for bit in bits]
    if len(coded) % 2:
        coded = coded[:-1]
    steps = len(coded) // 2
    if steps == 0:
        return []

    inf = 10**9
    metrics = {0: 0, 1: inf, 2: inf, 3: inf}
    paths = {0: [], 1: [], 2: [], 3: []}

    for i in range(steps):
        received = coded[2 * i : 2 * i + 2]
        next_metrics = {0: inf, 1: inf, 2: inf, 3: inf}
        next_paths = {0: [], 1: [], 2: [], 3: []}
        for state, metric in metrics.items():
            if metric >= inf:
                continue
            for bit in (0, 1):
                next_state, expected = _next_state_and_output(state, bit)
                distance = int(received[0] != expected[0]) + int(received[1] != expected[1])
                candidate = metric + distance
                if candidate < next_metrics[next_state]:
                    next_metrics[next_state] = candidate
                    next_paths[next_state] = paths[state] + [bit]
        metrics = next_metrics
        paths = next_paths

    final_state = 0 if terminate else min(metrics, key=metrics.get)
    decoded = paths[final_state]
    if terminate and len(decoded) >= 2:
        decoded = decoded[:-2]
    return decoded


def channel_encode(bits):
    """Rate-1/2 convolutional channel encoder, terminated to state zero."""
    return convolutional_encode(bits, terminate=True)


def channel_decode(bits):
    """Hard-decision Viterbi decoder for the default convolutional code."""
    return viterbi_decode(bits, terminate=True)


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode

