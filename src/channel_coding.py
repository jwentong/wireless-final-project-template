"""
信道编码模块别名 (供公开测试查找)
"""

# 从 channel_codec 导入顶层函数
from src.channel_codec import channel_encode, channel_decode, ConvolutionalEncoder, ViterbiDecoder

# 添加顶层别名
encode = channel_encode
decode = channel_decode
channel_coding_encode = channel_encode
channel_coding_decode = channel_decode
