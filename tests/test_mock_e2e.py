from src.source import source_encode, source_decode
from src.scramble import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame, xor_checksum
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn
from src.synchronization import detect_frame_start


class TestEndToEnd:

    def test_full_chain_12db_recovers_correct_text(self, sample_text):
        bits = source_encode(sample_text)
        scrambled = scramble(bits, 2026)
        checksum = xor_checksum(scrambled)
        coded = channel_encode(scrambled)
        frame = build_frame(coded, checksum)
        tx = qpsk_modulate(frame)
        rx = awgn(tx, 12.0, 2026)
        sync_idx = detect_frame_start(rx)
        frame_rx = rx[sync_idx:sync_idx + len(tx)]
        frame_bits = qpsk_demodulate(frame_rx)
        rx_coded, meta = parse_frame(frame_bits)
        rx_scrambled = channel_decode(rx_coded)
        rx_bits = descramble(rx_scrambled, 2026)
        recovered = source_decode(rx_bits[:len(bits)])
        assert recovered == sample_text

    def test_checksum_verification(self, sample_text):
        bits = source_encode(sample_text)
        scrambled = scramble(bits, 2026)
        checksum = xor_checksum(scrambled)
        coded = channel_encode(scrambled)
        frame = build_frame(coded, checksum)
        tx = qpsk_modulate(frame)
        rx = awgn(tx, 12.0, 2026)
        sync_idx = detect_frame_start(rx)
        frame_rx = rx[sync_idx:sync_idx + len(tx)]
        frame_bits = qpsk_demodulate(frame_rx)
        rx_coded, meta = parse_frame(frame_bits)
        rx_scrambled = channel_decode(rx_coded)
        assert xor_checksum(rx_scrambled) == meta["checksum_bits"]

    def test_metrics_fields_present(self, sample_text):
        bits = source_encode(sample_text)
        scrambled = scramble(bits, 2026)
        coded = channel_encode(scrambled)
        checksum = xor_checksum(scrambled)
        frame = build_frame(coded, checksum)
        tx = qpsk_modulate(frame)
        rx = awgn(tx, 12.0, 2026)
        sync_idx = detect_frame_start(rx)
        frame_rx = rx[sync_idx:sync_idx + len(tx)]
        frame_bits = qpsk_demodulate(frame_rx)
        _, meta = parse_frame(frame_bits)
        assert "length" in meta
        assert "checksum_pass" in meta
        assert "checksum_bits" in meta

    def test_different_seed_gives_different_result(self, sample_text):
        bits = source_encode(sample_text)
        scrambled_1 = scramble(bits, 100)
        scrambled_2 = scramble(bits, 200)
        assert scrambled_1 != scrambled_2

    def test_multiple_texts(self):
        texts = ["Hello, World!", "abc", "A" * 200, "你好"]
        for text in texts:
            bits = source_encode(text)
            scrambled = scramble(bits, 2026)
            checksum = xor_checksum(scrambled)
            coded = channel_encode(scrambled)
            frame = build_frame(coded, checksum)
            tx = qpsk_modulate(frame)
            rx = awgn(tx, 12.0, 2026)
            sync_idx = detect_frame_start(rx)
            frame_rx = rx[sync_idx:sync_idx + len(tx)]
            frame_bits = qpsk_demodulate(frame_rx)
            rx_coded, _ = parse_frame(frame_bits)
            rx_scrambled = channel_decode(rx_coded)
            rx_bits = descramble(rx_scrambled, 2026)
            recovered = source_decode(rx_bits[:len(bits)])
            assert recovered == text
