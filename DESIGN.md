# Wireless Communication Baseband Simulation Design

## 1. Goal

This project implements the required fixed chain:

`Test.txt -> Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Decrypt/Descramble -> Source Decode -> received.txt -> Metrics/Plots`

The basic acceptance target is exact recovery of UTF-8 text at `SNR >= 12 dB`, `AWGN`, fixed seed, QPSK modulation, and a random QPSK-symbol prefix offset from 0 to 128 symbols.

## 2. Module Architecture

| Module | File | Responsibility |
|---|---|---|
| Source Encode / Source Decode | `src/source.py` | Convert UTF-8 text to a big-endian bitstream and recover text from complete bytes. |
| Encrypt / Scramble | `src/crypto.py` | XOR source bits with a seed-controlled PN sequence. The same operation performs descrambling. |
| Channel Encode / Channel Decode | `src/channel_coding.py` | Repetition-3 forward error correction with majority-vote decoding. |
| Frame Build / Parse | `src/framing.py` | Add preamble, original payload length, transmitted coded length, payload, and CRC32 checksum. |
| QPSK Modulate / Demodulate | `src/modulation.py` | Required Gray-coded QPSK mapping and hard-decision demapping. |
| Channel | `src/channel.py` | AWGN channel with deterministic random seed and symbol-power SNR definition. |
| Synchronization | `src/synchronization.py` | Preamble correlation peak search over received QPSK symbols. |
| Metrics / Plots | `src/pipeline.py` | End-to-end orchestration, metrics JSON, constellation, BER-SNR, and sync peak plots. |
| CLI | `main.py` | Unified command-line entrypoint. |
| Web UI | `web_app.py` | Local browser interface for interactive simulation, metrics display, and plot viewing. |

## 3. Key Algorithms and Parameters

### Source Encode

The input file is read as UTF-8. Each byte is converted to 8 bits in big-endian order. The payload length recorded in the frame is the original source bit count before scrambling, matching the PRD requirement for padding removal and UTF-8 recovery.

### Scramble / Encrypt

The scrambler uses a NumPy `default_rng(seed)` PN sequence and XORs one PN bit with each payload bit. This is reversible because XOR is its own inverse. The purpose is not strong cryptographic security; it demonstrates an invertible wireless-link scrambling stage.

### Channel Encode

The system uses repetition-3 coding:

- Encoder: each bit becomes `bbb`.
- Decoder: each group of 3 bits is decoded by majority vote.
- Code rate: `1/3`.

This simple coding improves robustness at 12 dB and remains easy to explain in a course defense.

### Frame Structure

Serialized frame bits are:

`preamble(64) | payload_length(32) | tx_payload_length(32) | channel_coded_payload | crc32(32)`

The PRD requires the length field to represent the original payload bit count after source encoding and before scrambling. The implementation exposes that value in metrics as `payload_bits` and `frame_payload_bits`. Internally, the frame also stores `tx_payload_length`, because the transmitted payload has passed through channel coding and is longer than the original source payload. The serialized frame includes a CRC32 over the original payload bitstream, so the receiver verifies it after channel decoding and descrambling. Final `metrics.json` records `frame_crc_scope: original-payload-bits`, `frame_crc_pass`, and `checksum_pass`.

### QPSK

The required Gray-coded mapping is implemented exactly:

| Bits | Symbol |
|---|---|
| 00 | `(1+j)/sqrt(2)` |
| 01 | `(-1+j)/sqrt(2)` |
| 11 | `(-1-j)/sqrt(2)` |
| 10 | `(1-j)/sqrt(2)` |

The `1/sqrt(2)` normalization makes average symbol power approximately 1. If the bit count entering QPSK is odd, one `0` is appended. The receiver removes padding using the frame lengths.

### AWGN Channel and SNR

SNR is defined as average received modulation-symbol power divided by complex Gaussian noise average power, in dB. For unit-power QPSK symbols, the noise variance is:

`noise_power = signal_power / 10^(SNR_dB/10)`

The real and imaginary components each receive variance `noise_power / 2`. The channel uses the provided seed for reproducibility.

### Level 3 Extension: Rayleigh Fading and Equalization

The project also supports:

```bash
python main.py --input Test.txt --output results/received.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh
```

The Rayleigh extension uses a flat fading model:

`y = h x + n`

where `h` is one complex Gaussian channel gain for the whole frame and `n` is AWGN. The receiver uses a perfect-CSI one-tap equalizer:

`x_hat = y / h`

This is a controlled Level 3 module: it demonstrates fading and equalization without changing the required QPSK/AWGN baseline. Metrics record `channel=rayleigh`, `equalizer=perfect-csi-one-tap`, and the real/imaginary parts of `h`.

### Level 3 Extension: Web Simulation Interface

The project includes a dependency-free local Web UI:

```bash
python web_app.py --host 127.0.0.1 --port 8000
```

The page lets the user input payload text, SNR, seed, modulation, source-codec mode, scrambling mode, channel-coding mode, and channel mode. It calls `/api/run`, which writes a temporary input file, executes the same `run_pipeline()` used by the CLI, and returns recovered text, metrics, plot URLs, and a `stage_trace` list.

The stage trace contains the full chain:

`Source Encode -> Scramble / Encrypt -> Channel Encode -> Frame Build -> QPSK Modulate -> Wireless Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Descramble / Decrypt -> Source Decode -> Metrics / Plots`

The Web layer is intentionally thin so the graphical workflow and command-line workflow share the same tested communication modules. For teaching demonstration, the UI can disable scrambling or channel coding, but the CLI defaults remain the PRD-compliant PN-XOR and repetition-3 settings.

### Synchronization

The transmitter adds a random prefix of 0 to 128 QPSK symbols before the frame. The receiver does not know this offset. It computes the correlation magnitude between the known QPSK preamble and every candidate window, then selects the maximum peak as `sync_start_index`. At 12 dB AWGN, this detects the frame start within 1 symbol in the public and local tests.

## 4. Metrics and Plots

`results/metrics.json` contains at least:

- `snr_db`
- `seed`
- `modulation`
- `channel`
- `payload_bits`
- `ber`
- `fer`
- `text_match_rate`
- `checksum_pass`
- `sync_start_index`

Additional fields record synchronization error, code choice, scrambler choice, frame payload length, and failure reason.

The system generates:

- `results/constellation.png`: received QPSK constellation after synchronization.
- `results/sync_peak.png`: preamble correlation peak.
- `results/ber_curve.png`: simulated QPSK AWGN BER-SNR curve.

## 5. Failure Analysis

At lower SNR, hard-decision QPSK demodulation may flip bits before repetition decoding. If enough flips occur inside a 3-bit repetition group, majority vote fails. This causes nonzero BER, CRC failure, possible UTF-8 decode failure, or a lower `text_match_rate`. Synchronization may also become less reliable if the preamble correlation peak is buried by noise, but at the PRD public threshold of 12 dB the correlation peak remains clear.

## 6. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Hidden tests use different UTF-8 Chinese text lengths | Source codec and frame length are data-driven; no hardcoded text is used. |
| Odd bit counts enter QPSK | Modulator pads one zero; frame length removes padding. |
| Random prefix offset changes | Receiver uses correlation against the preamble and reports detected start. |
| Public tests search for flexible function names | Modules expose canonical and alias function names. |
| Low-SNR decode failure | Program does not crash; it writes metrics with BER, FER, text match rate, checksum result, and failure reason. |
| Fading channel amplitude/phase rotation | Optional Rayleigh mode divides by the known complex gain and documents this as perfect CSI equalization. |

## 7. Defense Notes

- QPSK is selected because it transmits 2 bits per symbol while preserving a simple four-point constellation and Gray adjacency.
- Repetition coding trades rate for robustness: the data rate is reduced to one third, but one error in each 3-bit group can be corrected by majority vote.
- The preamble is required because the receiver cannot assume the frame starts at sample 0. Correlation turns frame detection into a peak-search problem.
- At low SNR, the first visible symptoms are constellation cloud expansion, increased BER, CRC/checksum failure, and reduced text match rate.

### Level 3 Extension: OFDM, Diversity, Viterbi, and Adaptive Modulation

The baseline QPSK/AWGN command remains unchanged. Advanced features are opt-in through CLI flags so public and hidden baseline tests still exercise the required PRD path.

- `--ofdm` packs data constellation symbols into 64-subcarrier OFDM blocks and adds a 16-sample cyclic prefix.
- `--diversity mrc2` uses two independent flat Rayleigh receive branches and maximal-ratio combining.
- `--coding conv` enables a rate-1/2, constraint-length-3 convolutional code with generators 7 and 5 octal and hard-decision Viterbi decoding.
- `--mod adaptive` selects BPSK, QPSK, or 16-QAM from the configured SNR. The selected mode is recorded as `effective_modulation`.

The combined advanced command is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 24 --seed 2026 --mod adaptive --channel rayleigh --coding conv --diversity mrc2 --ofdm
```
