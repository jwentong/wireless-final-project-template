def _pn_sequence(length, seed):
    state = seed & 0x7FFF
    if state == 0:
        state = 1
    bits = []
    for _ in range(length):
        output = state & 1
        new_bit = ((state >> 14) ^ (state >> 13)) & 1
        state = ((state << 1) | new_bit) & 0x7FFF
        bits.append(output)
    return bits

def scramble(bits, seed=2026):
    pn = _pn_sequence(len(bits), seed)
    return [b ^ p for b, p in zip(bits, pn)]

def descramble(bits, seed=2026):
    return scramble(bits, seed)

def encrypt(bits, seed=2026):
    return scramble(bits, seed)

def decrypt(bits, seed=2026):
    return scramble(bits, seed)

def scramble_bits(bits, seed=2026):
    return scramble(bits, seed)

def descramble_bits(bits, seed=2026):
    return scramble(bits, seed)
