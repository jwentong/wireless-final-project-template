# Experiment Report

## 1. Experiment Goal

The goal of this experiment is to verify the required AWGN baseline wireless
file transmission system and then add a Level 3 extension using flat Rayleigh
fading with simple one-tap equalization.

The baseline command must remain unchanged:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

The Level 3 Rayleigh command is:

```bash
python main.py --input Test.txt --output results/received_rayleigh.txt --snr 12 --seed 2026 --mod qpsk --channel rayleigh
```

The AWGN baseline remains the acceptance path and writes the final
`results/metrics.json`. Rayleigh is an extension comparison path; after a
Rayleigh run, its metrics are also archived as `results/metrics_rayleigh.json`.

## 2. Baseline AWGN Result

Under SNR = 12 dB, AWGN, and seed = 2026, the baseline command recovered
`Test.txt` exactly at byte level.

Recorded metrics:

```text
channel = awgn
payload_bits = 6128
BER = 0.0
FER = 0.0
text_match_rate = 1.0
checksum_pass = true
sync_start_index = 109
```

This verifies that the required baseline design satisfies the main public
acceptance condition.

## 3. Rayleigh Fading Extension Design

The Level 3 extension adds a flat Rayleigh fading coefficient for each QPSK
symbol:

```text
h = (randn + j * randn) / sqrt(2)
```

The received symbol is:

```text
r = h * s + n
```

where `s` is the transmitted QPSK symbol and `n` is complex AWGN. The random
seed controls the fading and noise generation so that the experiment is
reproducible.

## 4. One-Tap Equalization Principle

In this simulation, the receiver uses known channel coefficients. For Rayleigh
mode, it applies one-tap equalization:

```text
r_eq = r / h
```

An epsilon value is used to avoid division by zero. This equalizer removes the
complex amplitude and phase rotation caused by flat fading when the channel
coefficient is reliable. However, if `h` is very small, equalization can amplify
noise, so residual bit errors may remain.

## 5. AWGN vs Rayleigh BER-SNR Comparison

The project generates:

```text
results/ber_curve.png
results/ber_curve_compare.png
```

`ber_curve_compare.png` compares AWGN and Rayleigh + one-tap equalization under
the same QPSK hard-decision demodulation. The Rayleigh curve is expected to be
worse than AWGN at the same SNR because deep fading can strongly amplify noise
after equalization.

For the actual Rayleigh file-transmission run at SNR = 12 dB and seed = 2026,
the metrics in `results/metrics_rayleigh.json` were:

```text
channel = rayleigh
equalization = one-tap
fading_model = flat_rayleigh
BER = 0.005711488250652741
FER = 1.0
text_match_rate = 0.028985507246376812
checksum_pass = false
failure_reason = utf8_decode_error
```

This result is not exact file recovery, but the program exits normally and
records the failure information.

## 6. Constellation Plot

`results/constellation.png` shows the received QPSK symbols used in the most
recent run. In AWGN mode, the constellation points cluster around the four
normalized QPSK decision regions. In Rayleigh mode, the plotted symbols are
after one-tap equalization; residual noise can still spread the points,
especially when fading coefficients are small.

## 7. Synchronization Peak Plot

`results/sync_peak.png` records the preamble correlation sequence. For the
baseline AWGN run at SNR = 12 dB and seed = 2026, the detected start index was
109, matching the generated prefix offset. For Rayleigh mode, equalization is
applied before synchronization.

## 8. Low-SNR Failure Analysis

At low SNR, QPSK hard decisions become unreliable. With Rayleigh fading, deep
fades can make the effective post-equalization noise much larger. When residual
bit errors remain after repetition-3 decoding, CRC32 fails and UTF-8 decoding
may produce replacement text or fail. The system should not hard-code a correct
output in this case; it records BER, FER, checksum status, text match rate, and
failure reason in `metrics.json`.

## 9. Summary

The AWGN baseline remains the required reliable path and still recovers
`Test.txt` exactly under the public baseline condition. The Rayleigh fading
extension adds a more challenging wireless channel and demonstrates one-tap
equalization. The Rayleigh run at SNR = 12 dB did not fully recover the file,
which is consistent with residual errors caused by fading and noise
enhancement. The result is recorded honestly in the metrics and plots.
