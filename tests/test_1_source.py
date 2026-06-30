from src.source_codec import text_to_bitstream, bitstream_to_text

with open("Test.txt", "r", encoding="utf-8") as f:
    original = f.read()

bits = text_to_bitstream(original)
restored = bitstream_to_text(bits)

print(f"原始字节数: {len(original.encode('utf-8'))}")
print(f"比特流长度: {len(bits)} bit")
print(f"可逆性验证: {'✅ 通过' if original == restored else '❌ 失败'}")