"""Channel coding module: Convolutional code (rate 1/2, K=7) with Viterbi decoding.

Uses the industry-standard CCSDS polynomials:
  - G0 = 0o171 (1111001) → output bit 0
  - G1 = 0o133 (1011011) → output bit 1

The Viterbi decoder uses hard-decision decoding with traceback depth = 5*K.
"""

import numpy as np

# Convolutional code generator polynomials (CCSDS standard, rate 1/2, K=7)
G0 = 0o171  # 1111001
G1 = 0o133  # 1011011
CONSTRAINT_LENGTH = 7
NUM_STATES = 1 << (CONSTRAINT_LENGTH - 1)  # 64 states
TRACEBACK_DEPTH = 5 * CONSTRAINT_LENGTH  # 35


def _conv_encode_one(input_bit: int, state: int) -> tuple[int, int, int]:
    """Encode one input bit.

    Args:
        input_bit: The input bit (0 or 1).
        state: Current encoder state (6 bits, 0-63).

    Returns:
        Tuple of (output_bit_0, output_bit_1, next_state).
    """
    # Shift register: MSB is oldest, LSB is newest
    shift_reg = ((state << 1) | int(input_bit)) & ((1 << CONSTRAINT_LENGTH) - 1)

    # Compute output bits using generator polynomials
    out0 = bin(shift_reg & G0).count("1") % 2
    out1 = bin(shift_reg & G1).count("1") % 2

    # New state is the lower (K-1) bits of the shift register
    next_state = shift_reg & (NUM_STATES - 1)

    return out0, out1, next_state


def channel_encode(bits: list[int]) -> list[int]:
    """Convolutional encode a bitstream (rate 1/2, K=7).

    Uses CCSDS standard polynomials (171, 133 octal).

    Args:
        bits: Input bit list.

    Returns:
        Encoded bit list (twice the length of input).
    """
    state = 0
    encoded = []
    for b in bits:
        out0, out1, state = _conv_encode_one(int(b), state)
        encoded.append(out0)
        encoded.append(out1)
    return encoded


def _hamming_dist(a: int, b: int) -> int:
    """Hamming distance between two bits (0 or 1)."""
    return 0 if int(a) == int(b) else 1


def channel_decode(bits: list[int]) -> list[int]:
    """Viterbi decode a convolutionally encoded bitstream.

    Uses hard-decision Viterbi algorithm with full traceback.

    Args:
        bits: Encoded bit list (must have even length).

    Returns:
        Decoded bit list (half the length of input, approximately).
    """
    if len(bits) < 2:
        return []

    # Ensure even length
    encoded = bits[:len(bits) - (len(bits) % 2)]
    num_stages = len(encoded) // 2

    if num_stages == 0:
        return []

    # Path metrics (log probability, lower = better)
    path_metrics = np.full(NUM_STATES, np.inf)
    path_metrics[0] = 0.0

    # Survivor paths: prev_state[t][s] = previous state, prev_bit[t][s] = input bit
    prev_state = np.zeros((num_stages + 1, NUM_STATES), dtype=int)
    prev_bit = np.zeros((num_stages + 1, NUM_STATES), dtype=int)

    # Forward pass: Add-Compare-Select
    for t in range(num_stages):
        r0 = int(encoded[2 * t])
        r1 = int(encoded[2 * t + 1])

        new_metrics = np.full(NUM_STATES, np.inf)

        for state in range(NUM_STATES):
            current_metric = path_metrics[state]
            if np.isinf(current_metric):
                continue

            for input_bit in [0, 1]:
                out0, out1, next_state = _conv_encode_one(input_bit, state)
                branch_cost = _hamming_dist(r0, out0) + _hamming_dist(r1, out1)
                candidate = current_metric + branch_cost

                if candidate < new_metrics[next_state]:
                    new_metrics[next_state] = candidate
                    prev_state[t + 1, next_state] = state
                    prev_bit[t + 1, next_state] = input_bit

        path_metrics = new_metrics

    # Traceback: start from the state with best (minimum) path metric
    best_state = int(np.argmin(path_metrics))
    decoded = []

    for t in range(num_stages, 0, -1):
        decoded.append(int(prev_bit[t, best_state]))
        best_state = prev_state[t, best_state]

    decoded.reverse()
    return decoded


# Alternative function names for test discovery
def encode(bits: list[int]) -> list[int]:
    """Alias for channel_encode."""
    return channel_encode(bits)


def decode(bits: list[int]) -> list[int]:
    """Alias for channel_decode."""
    return channel_decode(bits)


def encode_bits(bits: list[int]) -> list[int]:
    """Alias for channel_encode."""
    return channel_encode(bits)


def decode_bits(bits: list[int]) -> list[int]:
    """Alias for channel_decode."""
    return channel_decode(bits)


def fec_encode(bits: list[int]) -> list[int]:
    """Alias for channel_encode."""
    return channel_encode(bits)


def fec_decode(bits: list[int]) -> list[int]:
    """Alias for channel_decode."""
    return channel_decode(bits)
