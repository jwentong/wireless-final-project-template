from src.source import source_encode, source_decode


def test_roundtrip_chinese():
    text = "无线通信技术"
    assert source_decode(source_encode(text)) == text


def test_roundtrip_mixed():
    text = "Hello 世界 123 ！@#"
    assert source_decode(source_encode(text)) == text


def test_length_multiple_of_8():
    assert len(source_encode("abc无")) % 8 == 0


def test_empty_string():
    assert source_decode(source_encode("")) == ""


def test_roundtrip_emoji():
    text = "通信📡测试"
    assert source_decode(source_encode(text)) == text
