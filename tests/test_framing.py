from src.framing import build_frame, parse_frame
from src.modulation import qpsk_demodulate, qpsk_modulate


def test_frame_round_trip_odd_payload_after_qpsk_padding():
    bits = [1, 0, 1, 1, 0] * 51
    frame = build_frame(bits)
    symbols = qpsk_modulate(frame["bits"])
    recovered_frame_bits = qpsk_demodulate(symbols)
    parsed = parse_frame(recovered_frame_bits)
    assert parsed["payload"] == bits
    assert parsed["length"] == len(bits)
