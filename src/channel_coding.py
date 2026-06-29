"""Channel coding (forward error correction).

Two schemes:
  * ``conv`` (default): convolutional code K=7, rate 1/2, generators (171,133)
    octal, terminated with K-1 zero tail bits and decoded by the hard-decision
    Viterbi algorithm. Provides ~4-5 dB coding gain; main link.
  * ``hamming``: Hamming(7,4), corrects one bit error per 7-bit block; baseline
    used for comparison experiments.

``channel_encode``/``channel_decode`` are the unified entry points; the scheme
keeps ``decode(encode(b))[:len(b)] == b`` in the noiseless case.
"""
from __future__ import annotations

# Convolutional code parameters
_K = 7
_G = [0o171, 0o133]
_STATE_MASK = (1 << (_K - 1)) - 1  # 6-bit state
_REG_MASK = (1 << _K) - 1


def _parity(x: int) -> int:
    return bin(x).count("1") & 1


def conv_encode(bits: list[int]) -> list[int]:
    """Convolutional encode with zero-tail termination. Output length = 2*(N+K-1)."""
    out: list[int] = []
    reg = 0
    for b in list(bits) + [0] * (_K - 1):
        reg = ((reg << 1) | int(b)) & _REG_MASK
        for g in _G:
            out.append(_parity(reg & g))
    return out


# Precompute trellis transitions: (state, input) -> (next_state, 2-bit output)
_NEXT = [[0, 0] for _ in range(_STATE_MASK + 1)]
_OUT = [[0, 0] for _ in range(_STATE_MASK + 1)]
for _s in range(_STATE_MASK + 1):
    for _b in range(2):
        _reg = ((_s << 1) | _b) & _REG_MASK
        _NEXT[_s][_b] = _reg & _STATE_MASK
        _OUT[_s][_b] = (_parity(_reg & _G[0]) << 1) | _parity(_reg & _G[1])


def viterbi_decode(coded: list[int]) -> list[int]:
    """Hard-decision Viterbi decode. Returns information bits (tail removed)."""
    coded = [int(c) for c in coded]
    n_steps = len(coded) // 2
    n_states = _STATE_MASK + 1
    inf = float("inf")
    pm = [inf] * n_states
    pm[0] = 0.0
    survivors: list[list[tuple[int, int]]] = []
    for t in range(n_steps):
        r = (coded[2 * t] << 1) | coded[2 * t + 1]
        new_pm = [inf] * n_states
        surv: list[tuple[int, int]] = [(-1, 0)] * n_states
        for s in range(n_states):
            if pm[s] == inf:
                continue
            for b in range(2):
                ns = _NEXT[s][b]
                metric = pm[s] + bin(_OUT[s][b] ^ r).count("1")
                if metric < new_pm[ns]:
                    new_pm[ns] = metric
                    surv[ns] = (s, b)
        pm = new_pm
        survivors.append(surv)
    # Traceback from the all-zero state (guaranteed by zero-tail termination)
    state = 0
    rev: list[int] = []
    for t in range(n_steps - 1, -1, -1):
        prev, b = survivors[t][state]
        rev.append(b)
        state = prev
    bits = rev[::-1]
    return bits[: -(_K - 1)] if len(bits) >= _K - 1 else bits


# ----------------------------- Hamming(7,4) -----------------------------
def hamming_encode(bits: list[int]) -> list[int]:
    """Hamming(7,4) encode; pads input to a multiple of 4."""
    bits = [int(b) for b in bits]
    while len(bits) % 4 != 0:
        bits.append(0)
    out: list[int] = []
    for i in range(0, len(bits), 4):
        d0, d1, d2, d3 = bits[i:i + 4]
        p1 = d0 ^ d1 ^ d3
        p2 = d0 ^ d2 ^ d3
        p3 = d1 ^ d2 ^ d3
        out += [p1, p2, d0, p3, d1, d2, d3]
    return out


def hamming_decode(bits: list[int]) -> list[int]:
    """Hamming(7,4) decode; corrects one error per 7-bit block."""
    bits = [int(b) for b in bits]
    out: list[int] = []
    for i in range(0, len(bits) - 6, 7):
        c = bits[i:i + 7]
        s1 = c[0] ^ c[2] ^ c[4] ^ c[6]
        s2 = c[1] ^ c[2] ^ c[5] ^ c[6]
        s3 = c[3] ^ c[4] ^ c[5] ^ c[6]
        syn = (s3 << 2) | (s2 << 1) | s1
        if syn:
            c[syn - 1] ^= 1
        out += [c[2], c[4], c[5], c[6]]
    return out


# ----------------------------- Unified API -----------------------------
def channel_encode(bits: list[int], scheme: str = "conv") -> list[int]:
    """Encode with the selected FEC scheme ('conv' default, or 'hamming')."""
    if scheme == "hamming":
        return hamming_encode(bits)
    return conv_encode(bits)


def channel_decode(bits: list[int], scheme: str = "conv") -> list[int]:
    """Decode with the selected FEC scheme ('conv' default, or 'hamming')."""
    if scheme == "hamming":
        return hamming_decode(bits)
    return viterbi_decode(bits)
