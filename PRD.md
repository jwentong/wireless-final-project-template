# PRD Summary

This project follows the Word PRD `PRD.docx` / `无线通信技术期末项目PRD.docx`.

## Required Chain

`Test.txt -> Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Decrypt/Descramble -> Source Decode -> received.txt -> Metrics/Plots`

## Required CLI

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

## Required Outputs

- `results/received.txt`
- `results/metrics.json`
- At least two plots among `constellation.png`, `ber_curve.png`, and `sync_peak.png`

This implementation generates all three plots.

## Scoring Targets

- Level 1: end-to-end QPSK/AWGN system with synchronization, coding, metrics, and file recovery.
- Level 2: scrambling, plots, mock testing, and design revision records.
- Level 3: optional Rayleigh flat fading channel with perfect-CSI one-tap equalization.

