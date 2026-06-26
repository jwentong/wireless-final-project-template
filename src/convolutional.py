def _parity(value: int) -> int:
    return value.bit_count() & 1


def convolutional_encode(bits: list[int]) -> list[int]:
    """Rate-1/2, constraint-length-3 convolutional encoder.

    Generator polynomials are 111 and 101 in binary. Two zero tail bits return
    the encoder to the all-zero state, which makes Viterbi termination stable.
    """
    state = 0
    encoded: list[int] = []
    for raw_bit in list(bits) + [0, 0]:
        bit = int(raw_bit) & 1
        reg = (bit << 2) | state
        encoded.append(_parity(reg & 0b111))
        encoded.append(_parity(reg & 0b101))
        state = ((bit << 1) | (state >> 1)) & 0b11
    return encoded


def viterbi_decode(encoded_bits: list[int]) -> list[int]:
    pairs = [encoded_bits[i : i + 2] for i in range(0, len(encoded_bits) - 1, 2)]
    inf = 10**9
    metrics = {0: 0, 1: inf, 2: inf, 3: inf}
    paths: dict[int, list[int]] = {0: [], 1: [], 2: [], 3: []}

    for pair in pairs:
        next_metrics = {0: inf, 1: inf, 2: inf, 3: inf}
        next_paths: dict[int, list[int]] = {0: [], 1: [], 2: [], 3: []}
        for state, metric in metrics.items():
            if metric >= inf:
                continue
            for bit in (0, 1):
                reg = (bit << 2) | state
                expected = [_parity(reg & 0b111), _parity(reg & 0b101)]
                distance = (expected[0] != int(pair[0])) + (expected[1] != int(pair[1]))
                next_state = ((bit << 1) | (state >> 1)) & 0b11
                candidate = metric + int(distance)
                if candidate < next_metrics[next_state]:
                    next_metrics[next_state] = candidate
                    next_paths[next_state] = paths[state] + [bit]
        metrics = next_metrics
        paths = next_paths

    best_state = min(metrics, key=metrics.get)
    decoded = paths[best_state]
    return decoded[:-2] if len(decoded) >= 2 else decoded


conv_encode = convolutional_encode
conv_decode = viterbi_decode
