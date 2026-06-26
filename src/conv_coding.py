"""Convolutional code (K=3, g1=7, g2=5) with hard-decision Viterbi decoding."""

from __future__ import annotations

G1 = 0b111  # 7 oct
G2 = 0b101  # 5 oct
K = 3
N_STATES = 2 ** (K - 1)


def _parity(value: int) -> int:
    return bin(value).count("1") & 1


def _next_state(state: int, bit: int) -> int:
    return ((state << 1) | bit) & (N_STATES - 1)


def _outputs(state: int, bit: int) -> tuple[int, int]:
    reg = (state << 1) | bit
    o1 = _parity(reg & G1)
    o2 = _parity(reg & G2)
    return o1, o2


def conv_encode(bits: list[int]) -> list[int]:
    state = 0
    out: list[int] = []
    for bit in bits:
        b = int(bit)
        o1, o2 = _outputs(state, b)
        out.extend([o1, o2])
        state = _next_state(state, b)
    # Tail-biting flush
    for _ in range(K - 1):
        o1, o2 = _outputs(state, 0)
        out.extend([o1, o2])
        state = _next_state(state, 0)
    return out


def viterbi_decode(bits: list[int]) -> list[int]:
    """Hard-decision Viterbi; returns decoded bits (excluding tail flush)."""
    if not bits:
        return []
    # Number of input bits inferred from length and tail
    n_steps = len(bits) // 2
    inf = 10**9
    path_metric = [inf] * N_STATES
    path_metric[0] = 0
    paths: list[list[tuple[int, int]]] = [[] for _ in range(N_STATES)]

    for t in range(n_steps):
        o0, o1 = int(bits[2 * t]), int(bits[2 * t + 1])
        new_metric = [inf] * N_STATES
        new_paths: list[list[tuple[int, int]]] = [[] for _ in range(N_STATES)]
        for state in range(N_STATES):
            if path_metric[state] >= inf:
                continue
            for bit in (0, 1):
                ns = _next_state(state, bit)
                e0, e1 = _outputs(state, bit)
                cost = path_metric[state] + (e0 != o0) + (e1 != o1)
                if cost < new_metric[ns]:
                    new_metric[ns] = cost
                    new_paths[ns] = paths[state] + [(state, bit)]
        path_metric = new_metric
        paths = new_paths

    best_state = int(min(range(N_STATES), key=lambda s: path_metric[s]))
    decoded_bits = [bit for _, bit in paths[best_state]]
    # Remove tail bits
    if len(decoded_bits) >= K - 1:
        decoded_bits = decoded_bits[: -(K - 1)]
    return decoded_bits
