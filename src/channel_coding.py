import numpy as np


def channel_encode(bits):
    arr = np.asarray(bits, dtype=np.uint8) & 1
    return np.repeat(arr, 3).astype(int).tolist()


def channel_decode(bits):
    arr = np.asarray(bits, dtype=np.uint8) & 1
    usable = len(arr) - (len(arr) % 3)
    if usable <= 0:
        return []
    groups = arr[:usable].reshape(-1, 3)
    return (np.sum(groups, axis=1) >= 2).astype(int).tolist()


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode

