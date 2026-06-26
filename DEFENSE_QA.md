# Defense Q&A Notes

This document answers the teacher's likely defense questions and points to code or experiment evidence.

## 1. Why choose QPSK for the basic system?

QPSK is a good baseline because it sends 2 bits per symbol while keeping the constellation simple enough for reliable hard-decision demodulation. Compared with BPSK, QPSK improves spectral efficiency. Compared with 16-QAM, QPSK is easier to recover at moderate SNR and is more suitable for a basic required system.

The project uses the PRD-required Gray-coded QPSK mapping:

| Bits | Symbol |
|---|---|
| `00` | `(1+j)/sqrt(2)` |
| `01` | `(-1+j)/sqrt(2)` |
| `11` | `(-1-j)/sqrt(2)` |
| `10` | `(1-j)/sqrt(2)` |

The `1/sqrt(2)` factor normalizes average symbol power to about 1, so the AWGN SNR definition is clean: symbol average power divided by complex noise average power.

Code reference: `src/modulation.py`.

## 2. How does the frame structure support synchronization, length identification, and error detection?

The frame is:

```text
preamble(64) | payload_length(32) | tx_payload_length(32) | channel_coded_payload | crc32(32)
```

- `preamble`: known sequence used by the receiver for correlation-based synchronization.
- `payload_length`: original source payload bit length, used to remove QPSK padding and recover UTF-8 text.
- `tx_payload_length`: transmitted coded payload length, needed because channel coding expands the payload.
- `crc32`: detects payload corruption. Final `checksum_pass` also compares the recovered original source bitstream.

Code reference: `src/framing.py`, `src/synchronization.py`.

## 3. What problem does channel coding solve? How do code rate and correction ability affect efficiency?

Channel coding adds redundancy so the receiver can correct noise-induced bit errors. This project uses repetition-3:

```text
0 -> 000
1 -> 111
```

The receiver uses majority voting for every 3 received bits. If at most one bit in a group is wrong, the original bit is recovered.

The tradeoff is efficiency:

- Code rate is `1/3`.
- More symbols are transmitted for the same payload.
- Reliability improves, but throughput decreases.

Experiment evidence:

```bash
python scripts/run_experiments.py --input Test.txt --output-dir results/experiments --snrs 0,3,6,9,12,15 --seed 2026
```

The generated `results/experiments/coding_gain.png` compares coded and uncoded AWGN BER.

## 4. When SNR decreases, which module fails first? How can it be located?

The earliest failure is usually QPSK demodulation. Lower SNR spreads constellation points around their ideal locations. Once points cross the I/Q decision boundaries, bit errors appear.

Debugging order:

1. Check `results/constellation.png`: wide clusters or crossed decision regions suggest demodulation errors.
2. Check `ber` in `metrics.json`.
3. Check `sync_error_symbols`: if nonzero, synchronization failed before demodulation.
4. Check `checksum_pass` and `frame_crc_pass_before_fec`.
5. Check `text_match_rate` to measure final user-visible recovery.

Experiment evidence:

- `results/experiments/snr_text_match.png`
- `results/experiments/experiment_summary.csv`

## 5. If `received.txt` becomes garbled, what is the troubleshooting order?

1. Confirm CLI parameters: `--mod qpsk`, `--channel awgn`, expected `--snr`, expected `--seed`.
2. Check synchronization: `sync_start_index`, `sync_expected_offset`, `sync_error_symbols`.
3. Check frame parsing: payload length and transmitted payload length.
4. Check channel decode output length.
5. Check descrambling seed consistency.
6. Check `ber` and `checksum_pass`.
7. If BER is nonzero, inspect constellation and SNR; if BER is zero but text fails, inspect UTF-8 source decode and length trimming.

## 6. What design defects did mock testing reveal? How were they fixed?

Mock testing found that a single length field was not enough after channel coding. The original payload bit length is required by the PRD, but the transmitted payload is longer after repetition coding.

Design revision:

- Keep `payload_length` for the original source bitstream.
- Add `tx_payload_length` for the transmitted channel-coded payload.
- Use both lengths during receive parsing and source recovery.

This fixed odd-length payload handling, QPSK padding removal, and channel-coded frame parsing.

Document reference: `MOCK_TEST_REPORT.md`.

## 7. Which AI-generated code was kept, modified, or rejected?

Kept:

- Modular source codec, scrambler, channel coding, framing, QPSK, channel, synchronization, and pipeline structure.
- Tests for public requirements and extension behavior.
- Web UI and interactive stage trace.

Modified:

- Frame structure was revised to add `tx_payload_length`.
- `checksum_pass` was changed to reflect recovered original payload correctness, while `frame_crc_pass_before_fec` is retained for diagnostics.
- Web UI was expanded from a simple run form into an interactive lesson console with SVG diagrams and per-stage live values.

Rejected / avoided:

- Directly copying `Test.txt` to `received.txt`.
- Hardcoding public-test input/output.
- Adding heavy Web dependencies such as Flask, so the project remains simple to run.

Document reference: `AI_LOG.md`.

## 8. What extensions were added for higher scoring?

1. Rayleigh flat fading channel:

```bash
python main.py --input Test.txt --output results/received.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh
```

It models `y = hx + n` and uses perfect-CSI one-tap equalization `x_hat = y / h`.

2. Interactive Web simulation interface:

```bash
python web_app.py --host 127.0.0.1 --port 8000
```

The interface lets the operator interact with the full communication chain, click each stage, read explanations, inspect SVG diagrams, and see live metrics from the latest run.

3. Experiment runner:

```bash
python scripts/run_experiments.py --input Test.txt --output-dir results/experiments --snrs 0,3,6,9,12,15 --seed 2026
```

It generates:

- `results/experiments/experiment_summary.csv`
- `results/experiments/experiment_summary.json`
- `results/experiments/snr_text_match.png`
- `results/experiments/coding_gain.png`


## Level 3 Advanced Module Defense Points

The project implements all advanced module examples listed in the PRD:

- OFDM: symbols are arranged on 64 subcarriers, transformed by IFFT, and protected by a 16-sample cyclic prefix. The receiver removes CP and applies FFT.
- Diversity: `mrc2` simulates two independent Rayleigh receive branches and combines them with maximal-ratio combining.
- Convolutional Viterbi: `--coding conv` uses a rate-1/2, K=3 convolutional encoder and hard-decision Viterbi decoder.
- Adaptive modulation: `--mod adaptive` selects BPSK, QPSK, or 16-QAM according to SNR and records the selected mode in metrics.
- Graphical interface: the Web UI exposes modulation, coding, OFDM, channel, and diversity controls.

Combined command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 24 --seed 2026 --mod adaptive --channel rayleigh --coding conv --diversity mrc2 --ofdm
```
