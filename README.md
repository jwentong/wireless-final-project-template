# Wireless Communication Final Project

This project implements an end-to-end wireless communication baseband simulation system. It sends the UTF-8 payload in `Test.txt` through source coding, scrambling, channel coding, framing, QPSK modulation, wireless channel simulation, synchronization, demodulation, decoding, descrambling, and text recovery into `results/received.txt`.

## Implemented Features

- UTF-8 Source Encode / Source Decode.
- PN-sequence XOR Scramble / Descramble.
- Repetition-3 channel coding and majority-vote decoding.
- Frame fields: preamble, original payload length, transmitted payload length, payload, CRC32.
- PRD-required Gray-coded QPSK.
- AWGN channel with symbol-power SNR definition.
- Preamble-correlation synchronization for random 0-128 QPSK-symbol prefix offsets.
- Level 3 extension: Rayleigh flat fading plus perfect-CSI one-tap equalization.
- Level 3 extension: local Web simulation interface.
- `metrics.json`, constellation plot, BER-SNR curve, and synchronization peak plot.

## CLI Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Required baseline command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Rayleigh extension:

```bash
python main.py --input Test.txt --output results/received.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh
```

## Web Interface

Start the local simulator UI:

```bash
python web_app.py --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The Web page supports a complete operation chain:

```text
Source Encode -> Scramble / Encrypt -> Channel Encode -> Frame Build
-> QPSK Modulate -> Wireless Channel -> Synchronization
-> QPSK Demodulate -> Channel Decode -> Descramble / Decrypt
-> Source Decode -> Metrics / Plots
```

The operator can input custom text, adjust SNR and seed, choose AWGN or Rayleigh channel, choose PN-XOR scrambling or demo-mode no scrambling, choose repetition-3 channel coding or demo-mode no coding, then inspect every stage's bit/symbol counts, recovered text, metrics, constellation plot, BER-SNR curve, and synchronization peak.

The Web interface also includes an interactive lesson panel. Each communication stage is clickable and shows:

- a small SVG schematic diagram;
- a paragraph explaining the stage's communication role;
- the key formula or mapping rule;
- live values from the latest simulation run.

## Extension Experiments

Run the extra experiment suite:

```bash
python scripts/run_experiments.py --input Test.txt --output-dir results/experiments --snrs 0,3,6,9,12,15 --seed 2026
```

It generates evidence for SNR degradation, coding gain, and the Rayleigh extension:

```text
results/experiments/experiment_summary.csv
results/experiments/experiment_summary.json
results/experiments/snr_text_match.png
results/experiments/coding_gain.png
```

## Tests

Local tests:

```bash
pytest tests -q
```

Teacher public tests:

```bash
pytest public_tests -q
```

## Outputs

The simulator generates:

```text
results/received.txt
results/metrics.json
results/constellation.png
results/ber_curve.png
results/sync_peak.png
```

## Documents

- `PRD.md`: PRD summary.
- `DESIGN.md`: architecture, module interfaces, algorithm choices, and risks.
- `TEST_PLAN.md`: test plan and hidden-test considerations.
- `MOCK_TEST_REPORT.md`: mock tests and design revision record.
- `REPORT.md`: experiment analysis and failure explanation.
- `DEFENSE_QA.md`: answers to likely defense questions.
- `AI_LOG.md`: AI-assisted development log.

## Academic Integrity Note

The project does not directly copy `Test.txt` to `received.txt`. All outputs come from the implemented communication chain. Before opening the Pull Request, fill in your student ID, name, GitHub username, fork URL, and branch in `.github/pull_request_template.md`.

## Level 3 Advanced Modules Completed

This project now includes every advanced module listed in the PRD examples:

- Rayleigh flat fading channel.
- Perfect-CSI one-tap equalization for single-branch Rayleigh.
- Two-branch receive diversity with maximal-ratio combining (`mrc2`).
- OFDM modulation with FFT size 64 and cyclic prefix length 16.
- Rate-1/2 convolutional code with hard-decision Viterbi decoding.
- Adaptive modulation: BPSK below 6 dB, QPSK from 6 to below 14 dB, and 16-QAM from 14 dB upward.
- Local Web UI controls for advanced modulation, coding, OFDM, and diversity.

All advanced modules can be enabled together:

```bash
python main.py --input Test.txt --output results/received.txt --snr 24 --seed 2026 --mod adaptive --channel rayleigh --coding conv --diversity mrc2 --ofdm
```
