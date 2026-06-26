# MOCK TEST REPORT

## Mock Test 1: UTF-8 and Source Length

Mock input used mixed Chinese and ASCII text. The initial design risk was losing byte boundaries after QPSK padding. Revision: DESIGN.md now states that source bits are byte-aligned and the frame `length` field records the original payload bit count.

## Mock Test 2: QPSK Padding

Mock payloads with odd bit counts produced one padded QPSK bit. Issue found: if the receiver treated the full demodulated tail as payload, the checksum position shifted. Revision: frame parsing reads payload size from `length` and ignores padding after the checksum.

## Mock Test 3: Synchronization Offset

A mock channel prepended 25 random symbols before the preamble. The defect risk was assuming the receiver knew frame start. Revision: the receiver performs preamble correlation and records `sync_start_index`.

## Mock Test 4: Checksum and Channel Coding

Mock noisy QPSK decisions showed that checksum should verify the original payload, while repetition code protects the scrambled payload. Change adopted: CRC32 covers original source bits; repetition-3 majority decoding is used before descrambling.

## Mock Test 5: Rayleigh Flat Fading Reproducibility

The Level 3 mock test added `tests/test_rayleigh_equalizer.py` and checked that `rayleigh_flat()` is reproducible under a fixed seed. This avoids a grading/debugging risk where two runs of the same Rayleigh experiment would produce different fading and noise.

## Mock Test 6: Preamble-Based Channel Estimation

A known complex scalar channel was applied to known preamble symbols, then the receiver estimated it with the least-squares formula. The mock test confirmed the estimated channel is close to the true value. This validates the design revision that places equalization after synchronization and before QPSK demodulation.

## Mock Test 7: Rayleigh CLI and AWGN Regression

The Rayleigh CLI mock run used `--channel rayleigh` and wrote `results/received_rayleigh.txt`. The metrics report includes the new equalizer and channel estimation fields. Validation results after the extension were `tests 4 passed` and `public_tests 22 passed`, showing the added Level 3 module did not break the original AWGN baseline chain.
