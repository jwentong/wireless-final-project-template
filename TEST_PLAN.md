# TEST PLAN

## Unit Tests

- Source coding: encode Chinese and ASCII UTF-8 text to bits, assert bit length is divisible by 8, then decode and compare exact text.
- Scramble: XOR random bitstreams with PN sequence using seed 2026, descramble with the same seed, and compare exact bits.
- Channel coding: run repetition-3 encoding and majority decoding with no noise and with single-bit errors per triplet.
- Frame structure: check preamble, 32-bit length, payload, and CRC32 checksum fields; build and parse random even and odd payload lengths.
- QPSK: verify PRD Gray mapping quadrants and unit average symbol power; demodulate noiseless symbols and compare bits.
- AWGN: call the channel twice with the same SNR and seed and assert identical complex samples.
- Synchronization: prepend 0, 25, and random 0-128 noise symbols before a known preamble and assert detected start error is at most one symbol.

## Integration Tests

- End-to-end recovery: run `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn` and compare `received.txt` with `Test.txt`.
- Metrics: validate `metrics.json` contains the required fields and reports `text_match_rate == 1.0` at 12 dB.
- Plots: check at least `constellation.png` and `sync_peak.png` are generated and non-empty; `ber_curve.png` is also generated.
- Lower SNR robustness: run at lower SNR and require no crash, with BER/FER/checksum fields explaining possible failure.

## Level 3 Rayleigh Equalizer Tests

- Rayleigh reproducibility: call `rayleigh_flat()` twice with the same symbols, SNR, and seed, then assert the complex outputs match.
- Channel estimation correctness: generate a simple known flat channel `h`, compute `received = h * known_preamble`, and verify `estimate_flat_channel()` returns a value close to `h`.
- Equalizer CLI run: execute `python main.py --input Test.txt --output results/received_rayleigh.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh` and require normal exit.
- Metrics fields: in Rayleigh mode, check `metrics.json` reports `channel == "rayleigh"` and contains `equalizer`, `channel_estimation`, `estimated_channel_real`, `estimated_channel_imag`, and `rayleigh_fading`.
- Regression check: rerun `python -m pytest public_tests -q` and require the AWGN baseline public tests to remain at 22 passed.
