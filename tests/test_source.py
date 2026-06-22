from src.source import source_decode, source_encode


def test_utf8_round_trip():
    text = "中文QPSK测试\nWireless communication."
    bits = source_encode(text)
    assert len(bits) % 8 == 0
    assert source_decode(bits) == text
