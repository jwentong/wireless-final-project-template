from __future__ import annotations


CONSTRAINT_LENGTH = 3
TAIL_BITS = CONSTRAINT_LENGTH - 1
G1 = 0b111
G2 = 0b101
STATE_COUNT = 1 << (CONSTRAINT_LENGTH - 1)


def _parity(value: int) -> int:
    return int(value.bit_count() & 1)


def _transition(state: int, bit: int) -> tuple[int, tuple[int, int]]:
    reg = (int(bit) << (CONSTRAINT_LENGTH - 1)) | state
    out = (_parity(reg & G1), _parity(reg & G2))
    next_state = ((int(bit) << (CONSTRAINT_LENGTH - 2)) | (state >> 1)) & (STATE_COUNT - 1)
    return next_state, out


def conv_encode(bits: list[int]) -> list[int]:
    state = 0
    coded: list[int] = []
    for bit in [int(x) for x in bits] + [0] * TAIL_BITS:
        state, out = _transition(state, bit)
        coded.extend(out)
    return coded


def viterbi_decode(bits: list[int]) -> list[int]:
    coded = [int(x) for x in bits]
    usable = len(coded) - (len(coded) % 2)
    pairs = [tuple(coded[i : i + 2]) for i in range(0, usable, 2)]
    inf = 10**9
    metrics = [0] + [inf] * (STATE_COUNT - 1)
    traces: list[list[tuple[int, int] | None]] = []
    for pair in pairs:
        next_metrics = [inf] * STATE_COUNT
        trace: list[tuple[int, int] | None] = [None] * STATE_COUNT
        for state, metric in enumerate(metrics):
            if metric >= inf:
                continue
            for bit in (0, 1):
                next_state, out = _transition(state, bit)
                distance = int(out[0] != pair[0]) + int(out[1] != pair[1])
                candidate = metric + distance
                if candidate < next_metrics[next_state]:
                    next_metrics[next_state] = candidate
                    trace[next_state] = (state, bit)
        metrics = next_metrics
        traces.append(trace)
    state = 0 if metrics[0] < inf else min(range(STATE_COUNT), key=lambda item: metrics[item])
    decoded_rev: list[int] = []
    for trace in reversed(traces):
        item = trace[state]
        if item is None:
            break
        prev_state, bit = item
        decoded_rev.append(bit)
        state = prev_state
    decoded = list(reversed(decoded_rev))
    if len(decoded) >= TAIL_BITS:
        decoded = decoded[:-TAIL_BITS]
    return decoded
