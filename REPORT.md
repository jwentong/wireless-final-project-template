# Experiment Analysis Report

## 1. Experiment Setup

Required baseline command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Level 3 extension command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh
```

Web interface:

```bash
python web_app.py --host 127.0.0.1 --port 8000
```

The baseline system uses UTF-8 source coding, PN XOR scrambling, repetition-3 channel coding, a framed packet with preamble and length fields, Gray-coded QPSK, AWGN, preamble correlation synchronization, hard-decision QPSK demodulation, majority-vote decoding, descrambling, and UTF-8 source decoding.

## 2. Baseline Result

For the required 12 dB AWGN run, the generated `results/metrics.json` reports:

| Metric | Meaning | Expected public result |
|---|---|---|
| `ber` | Bit error rate after receive processing | `0.0` |
| `fer` | Frame-level failure indicator | `0.0` |
| `text_match_rate` | Character-level text recovery ratio | `1.0` |
| `checksum_pass` | Original payload bitstream check | `true` |
| `sync_error_symbols` | Detected start minus true random prefix | `0` or within 1 symbol |

These values mean the recovered `results/received.txt` is identical to `Test.txt` under the public acceptance condition.

## 3. Constellation Analysis

`results/constellation.png` shows the received QPSK symbols after synchronization. At 12 dB AWGN, the points cluster around the four ideal constellation locations:

- `00 -> (1+j)/sqrt(2)`
- `01 -> (-1+j)/sqrt(2)`
- `11 -> (-1-j)/sqrt(2)`
- `10 -> (1-j)/sqrt(2)`

Noise spreads each cluster. If SNR is reduced, the clusters expand toward the decision boundaries and bit errors become more likely.

## 4. BER-SNR Curve Analysis

`results/ber_curve.png` plots hard-decision QPSK BER under AWGN for several SNR values. The expected trend is monotonic improvement as SNR increases. The curve is generated from random bits using the same QPSK mapper/demapper, so it directly reflects the modulation decision reliability.

The end-to-end link performs better than uncoded hard-decision QPSK because the payload uses repetition-3 coding and majority-vote decoding. The tradeoff is reduced spectral efficiency: three transmitted coded bits carry one information bit.

## 5. Synchronization Peak Analysis

`results/sync_peak.png` plots preamble-correlation magnitude across candidate frame starts. The correct frame start produces the dominant peak because the known preamble aligns with the received preamble only at the true offset.

This satisfies the PRD requirement that the receiver cannot assume the frame start is known. The system records both `sync_start_index` and `sync_expected_offset` for reproducible debugging.

## 6. Level 3 Rayleigh Extension

The optional Rayleigh mode models a flat fading channel:

`y = h x + n`

where `h` is a complex Gaussian fading coefficient. This rotates and scales the whole constellation. The receiver applies a perfect-CSI one-tap equalizer:

`x_hat = y / h`

This module demonstrates the wireless-channel concept that fading is not just additive noise; it also changes amplitude and phase. Equalization reverses that channel effect when channel state information is available.

## 7. Web Interface Demonstration

The Web UI turns the project into an interactive simulation system. It allows the operator to enter arbitrary UTF-8 payload text, choose SNR and seed, switch between AWGN and Rayleigh channel modes, choose PN-XOR scrambling or demo-mode no scrambling, choose repetition-3 coding or demo-mode no coding, run the same pipeline used by the CLI, and inspect recovered text, metrics, constellation, BER-SNR curve, and synchronization peak.

The interface also displays a per-stage trace for Source Encode, Scramble / Encrypt, Channel Encode, Frame Build, QPSK Modulate, Wireless Channel, Synchronization, QPSK Demodulate, Channel Decode, Descramble / Decrypt, Source Decode, and Metrics / Plots. This makes the system suitable for classroom demonstration and defense explanation.

For each stage, the Web UI provides an interactive schematic diagram, a short explanatory paragraph, the key formula or mapping rule, and live values from the latest run. This makes the demonstration stronger than a pure script because the operator can explain what each block does while showing the corresponding measured bit counts, symbol counts, synchronization result, and metrics.

The Web layer does not reimplement modulation or decoding logic. It calls `run_pipeline()`, so graphical operation remains consistent with public-test behavior.

## 8. Failure and Debugging Analysis

When SNR is low, failures usually appear in this order:

1. QPSK constellation clusters become wide and cross decision boundaries.
2. Hard-decision demodulation creates bit errors.
3. Repetition-3 majority vote fails if at least two bits in a group are wrong.
4. CRC/checksum or payload comparison fails.
5. UTF-8 decoding may fail or the recovered text has a lower `text_match_rate`.

The recommended debugging order is:

1. Check `sync_start_index` and `sync_error_symbols`.
2. Check constellation plot and BER.
3. Check `checksum_pass` and `frame_crc_pass_before_fec`.
4. Check source bit length and QPSK padding removal.
5. Check whether the failure is expected from the selected SNR/channel.

## 9. Extension Experiment Evidence

The project includes an experiment runner:

```bash
python scripts/run_experiments.py --input Test.txt --output-dir results/experiments --snrs 0,3,6,9,12,15 --seed 2026
```

It compares:

- `awgn-coded`: required AWGN baseline with repetition-3 coding;
- `awgn-uncoded`: an ablation that disables FEC to show coding gain;
- `rayleigh-coded`: Rayleigh flat fading with one-tap equalization.

Generated outputs:

- `results/experiments/experiment_summary.csv`
- `results/experiments/experiment_summary.json`
- `results/experiments/snr_text_match.png`
- `results/experiments/coding_gain.png`

These plots and tables support the defense explanations about SNR degradation, channel-coding gain, and the Rayleigh extension.

## Level 3 All-Advanced Demonstration

The final implementation includes all optional advanced examples named by the PRD: Rayleigh fading, equalization, OFDM, receive diversity, convolutional Viterbi coding, adaptive modulation, and graphical interface support. The `advanced-all` experiment scenario enables adaptive modulation, convolutional Viterbi coding, OFDM, Rayleigh channel, and MRC2 diversity together.

Recommended demonstration command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 24 --seed 2026 --mod adaptive --channel rayleigh --coding conv --diversity mrc2 --ofdm
```

Key metrics to point out during defense are `requested_modulation`, `effective_modulation`, `channel_code`, `ofdm_enabled`, `diversity`, `equalizer`, `ber`, `text_match_rate`, and `checksum_pass`.
