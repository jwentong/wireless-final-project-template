from src.source import source_decode, source_encode


def test_source_roundtrip_smoke():
    text = "wireless QPSK UTF-8 test"
    assert source_decode(source_encode(text)) == text

