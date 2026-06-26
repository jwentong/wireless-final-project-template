"""Metrics computation module: BER, FER, text match rate, and checksum verification."""


def compute_ber(original_bits: list[int], recovered_bits: list[int]) -> float:
    """Compute Bit Error Rate.

    Args:
        original_bits: Original transmitted bits.
        recovered_bits: Received/recovered bits.

    Returns:
        BER as a float (0.0 to 1.0).
    """
    if len(original_bits) == 0:
        return 0.0
    min_len = min(len(original_bits), len(recovered_bits))
    errors = sum(1 for i in range(min_len) if int(original_bits[i]) != int(recovered_bits[i]))
    return errors / len(original_bits)


def compute_fer(original_bits: list[int], recovered_bits: list[int], frame_bits: int = None) -> float:
    """Compute Frame Error Rate.

    If original and recovered bits differ at all at this framing level, it's a frame error.
    For simplicity, returns 0.0 if bits match exactly, 1.0 otherwise.

    Args:
        original_bits: Original bits.
        recovered_bits: Recovered bits.
        frame_bits: Optional frame size for multi-frame support.

    Returns:
        FER as a float (0.0 or 1.0 for single frame).
    """
    if len(original_bits) == 0:
        return 0.0

    min_len = min(len(original_bits), len(recovered_bits))
    for i in range(min_len):
        if int(original_bits[i]) != int(recovered_bits[i]):
            return 1.0
    if len(original_bits) != len(recovered_bits):
        return 1.0
    return 0.0


def compute_text_match(original_text: str, recovered_text: str) -> float:
    """Compute text match rate.

    Args:
        original_text: Original UTF-8 text.
        recovered_text: Recovered UTF-8 text.

    Returns:
        1.0 if texts are identical, 0.0 otherwise.
    """
    return 1.0 if original_text == recovered_text else 0.0


def verify_checksum(payload_bytes: bytes, expected_checksum: int) -> bool:
    """Verify checksum of payload bytes.

    Args:
        payload_bytes: Original payload in bytes.
        expected_checksum: Expected 16-bit checksum value.

    Returns:
        True if checksum matches.
    """
    actual = sum(payload_bytes) & 0xFFFF
    return actual == expected_checksum
