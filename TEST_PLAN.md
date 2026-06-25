# Test Plan

## Unit Tests

1. Source codec: UTF-8 Chinese and English text must satisfy `source_decode(source_encode(text)) == text`.
2. Scramble codec: `descramble(scramble(bits, seed), seed)` must recover the original bits for multiple seeds.
3. Channel coding: convolutional encode/Viterbi decode must be noiseless reversible and recover the original prefix after trellis termination removal.
4. Frame structure: `build_frame` output must include preamble, length, payload, and CRC; `parse_frame(build_frame(payload))` must recover the original payload length.
5. QPSK: the four PRD bit pairs must map to the required quadrants with unit average power; noiseless demodulation must have zero BER.
6. AWGN: the same symbols, SNR, and seed must produce reproducible noisy symbols.
7. Synchronization: a frame with 0 to 128 random leading symbols must be detected within one QPSK symbol at SNR >= 12 dB.

## End-to-End Tests

1. Run `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn`.
2. Check that `results/received.txt` exactly matches `Test.txt`.
3. Check that `results/metrics.json` includes the required fields and records `text_match_rate = 1.0`.
4. Check that constellation, BER-SNR, and sync peak plots are generated.
5. Run low-SNR cases such as 0 dB and 3 dB. The program may not fully recover text, but it must not crash and must report BER, FER, text_match_rate, and checksum status.
6. Run different UTF-8 texts and lengths to protect against hidden validation inputs.

## Public and Hidden Test Strategy

The public tests are run with `pytest public_tests -q`. Hidden tests may change text, SNR, seed, and synchronization offset, so implementation must use the CLI arguments and must not hard-code public input or expected output.
