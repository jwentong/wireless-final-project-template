"""
单元测试 - 源编码模块
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.source_codec import source_encode, source_decode, count_bits


class TestSourceCodec:
    """源编码模块测试类"""

    def test_encode_empty_string(self):
        """测试空字符串编码"""
        bits = source_encode("")
        assert len(bits) == 0

    def test_decode_empty_bits(self):
        """测试空比特流解码"""
        text = source_decode(np.array([], dtype=np.int8))
        assert text == ""

    def test_encode_single_char(self):
        """测试单字符编码"""
        text = "A"
        bits = source_encode(text)
        assert len(bits) == 8  # ASCII 字符 = 8 bits

    def test_encode_chinese_text(self):
        """测试中文文本编码"""
        text = "无线通信"
        bits = source_encode(text)
        # 中文 UTF-8 编码通常每个字符 3 字节
        assert len(bits) % 8 == 0

    def test_encode_decode_reversible_ascii(self):
        """测试 ASCII 文本编解码可逆性"""
        text = "Hello World!"
        bits = source_encode(text)
        decoded = source_decode(bits)
        assert decoded == text

    def test_encode_decode_reversible_chinese(self):
        """测试中文文本编解码可逆性"""
        text = "无线通信技术课程"
        bits = source_encode(text)
        decoded = source_decode(bits)
        assert decoded == text

    def test_encode_decode_reversible_mixed(self):
        """测试中英文混合文本编解码可逆性"""
        text = "Hello 无线通信 World!"
        bits = source_encode(text)
        decoded = source_decode(bits)
        assert decoded == text

    def test_bitstream_length_is_multiple_of_8(self):
        """测试比特流长度是 8 的倍数"""
        text = "测试文本123"
        bits = source_encode(text)
        assert len(bits) % 8 == 0

    def test_count_bits(self):
        """测试比特计数"""
        text = "AB"  # 2 ASCII chars = 16 bits
        assert count_bits(text) == 16

    def test_decode_with_non_multiple_of_8_bits(self):
        """测试非 8 的倍数比特流解码"""
        # 提供非 8 的倍数的比特流
        bits = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1], dtype=np.int8)
        # 应该自动截断到 8 的倍数
        text = source_decode(bits)
        assert isinstance(text, str)

    def test_long_text(self):
        """测试长文本编解码"""
        text = "无线通信技术课程要求学生理解调制编码信道和接收机处理" * 10
        bits = source_encode(text)
        decoded = source_decode(bits)
        assert decoded == text

    def test_special_characters(self):
        """测试特殊字符编解码"""
        text = "特殊字符：！@#￥%……&*（）"
        bits = source_encode(text)
        decoded = source_decode(bits)
        assert decoded == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
