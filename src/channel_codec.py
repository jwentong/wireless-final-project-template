import numpy as np

# (7,4) 汉明码生成矩阵 G (4×7)，系统码形式：前4位为信息位，后3位为校验位
_GENERATOR_MATRIX = np.array([
    [1, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 1, 0, 1],
    [0, 0, 1, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1, 1]
], dtype=np.int8)

# (7,4) 汉明码校验矩阵 H (3×7)，与 G 严格对应
_PARITY_CHECK_MATRIX = np.array([
    [1, 1, 0, 1, 1, 0, 0],
    [1, 0, 1, 1, 0, 1, 0],
    [0, 1, 1, 1, 0, 0, 1]
], dtype=np.int8)

# 伴随式十进制值 → 错误比特索引（对应上述校验矩阵的列顺序）
_SYNDROME_TO_POS = {
    1: 6,
    2: 5,
    3: 2,
    4: 4,
    5: 1,
    6: 0,
    7: 3
}


def hamming_encode(info_bits: np.ndarray) -> np.ndarray:
    """
    (7,4) 汉明码编码
    :param info_bits: 信息比特流，长度需为 4 的整数倍（不足自动补 0）
    :return: 编码后的码字比特流
    """
    # 补零对齐到 4 的整数倍
    pad_len = (4 - len(info_bits) % 4) % 4
    if pad_len > 0:
        info_bits = np.append(info_bits, np.zeros(pad_len, dtype=np.int8))
    
    # 按 4 位分组编码
    codewords = []
    for i in range(0, len(info_bits), 4):
        group = info_bits[i:i+4]
        codeword = np.mod(group @ _GENERATOR_MATRIX, 2)
        codewords.append(codeword)
    
    return np.concatenate(codewords)


def hamming_decode(code_bits: np.ndarray) -> np.ndarray:
    """
    (7,4) 汉明码译码，可纠正 1 位随机比特错误
    :param code_bits: 接收的码字比特流，长度需为 7 的整数倍
    :return: 译码后的信息比特流（包含补零，需上层截断）
    """
    info_bits = []
    for i in range(0, len(code_bits), 7):
        codeword = code_bits[i:i+7].copy()
        if len(codeword) < 7:
            break
        
        # 计算伴随式
        syndrome = np.mod(_PARITY_CHECK_MATRIX @ codeword, 2)
        syndrome_val = int(syndrome[0]*4 + syndrome[1]*2 + syndrome[2])
        
        # 伴随式非零则查表定位并纠正错误位
        if syndrome_val != 0 and syndrome_val in _SYNDROME_TO_POS:
            error_pos = _SYNDROME_TO_POS[syndrome_val]
            codeword[error_pos] ^= 1
        
        # 提取前 4 位信息比特
        info_bits.append(codeword[:4])
    
    return np.concatenate(info_bits) if info_bits else np.array([], dtype=np.int8)