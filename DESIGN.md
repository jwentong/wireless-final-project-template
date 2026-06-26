# DESIGN.md

# Wireless Final Project Design

## 1. Project Overview

This project implements an end-to-end wireless communication baseband simulation system. The system reads a UTF-8 text file `Test.txt`, converts the file content into a bitstream, transmits it through a simulated wireless baseband chain, and reconstructs the received text as `results/received.txt`.

The required baseband chain is:

```text
Test.txt
-> Source Encode
-> Encrypt/Scramble
-> Channel Encode
-> Frame Build
-> QPSK Modulate
-> Channel
-> Synchronization
-> QPSK Demodulate
-> Channel Decode
-> Decrypt/Descramble
-> Source Decode
-> received.txt
-> Metrics/Plots
```

The baseline system targets reliable text recovery under the following public validation condition:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Under AWGN channel and SNR >= 12 dB, the expected result is that `results/received.txt` is exactly the same as the input `Test.txt`.

---

## 2. Design Goals

The system is designed according to the following goals:

1. Support a unified command-line interface for automatic testing.
2. Complete the full wireless baseband processing chain.
3. Avoid hard-coding any public test input or output.
4. Support variable UTF-8 text content and variable file length.
5. Support fixed random seed for reproducible experiments.
6. Generate required output files, metrics, and plots.
7. Keep the implementation modular and easy to explain during defense.

The baseline target level is Level 2:

- QPSK modulation and demodulation.
- AWGN channel with configurable SNR.
- Frame synchronization based on preamble correlation.
- Reversible scrambling.
- Channel coding and decoding.
- End-to-end file recovery.
- `metrics.json`.
- At least two visualization results.

---

## 3. Main Assumptions

1. The input file is a UTF-8 text file.
2. The baseline modulation is QPSK.
3. The baseline channel is AWGN.
4. The receiver does not know the frame start position in advance.
5. The channel may insert a random prefix of 0 to 128 QPSK symbols before the valid frame.
6. The system should not crash at low SNR. If recovery fails, it should still output metrics and failure information.
7. The system uses one frame for one input file in the baseline implementation.

---

## 4. Project Structure

The recommended project structure is:

```text
wireless-final-project/
  PRD.md
  DESIGN.md
  TEST_PLAN.md
  MOCK_TEST_REPORT.md
  AI_LOG.md
  Test.txt
  main.py
  src/
    __init__.py
    source_codec.py
    scrambler.py
    channel_codec.py
    frame.py
    modulation.py
    channel.py
    synchronization.py
    metrics.py
    plots.py
    utils.py
  tests/
  results/
    received.txt
    metrics.json
    constellation.png
    ber_curve.png
    sync_peak.png
```

The implementation may be adjusted according to the teacher's template repository, but the logical module boundaries should remain clear.

---

## 5. Module Design

## 5.1 Source Encoding Module

### Function

The source encoding module converts UTF-8 text into a binary bitstream and converts the recovered bitstream back to UTF-8 text.

### Transmitter

```text
input text -> UTF-8 bytes -> payload bits
```

Each byte is converted into 8 bits in big-endian order.

Example:

```text
byte 0x41 -> 01000001
```

### Receiver

```text
recovered payload bits -> UTF-8 bytes -> output text
```

The receiver uses the original payload bit length stored in the frame length field to remove any extra padding before UTF-8 decoding.

### Key Parameters

| Parameter | Value |
|---|---|
| Text encoding | UTF-8 |
| Bit order | Big-endian within each byte |
| Payload length unit | bit |

### Risks

1. Chinese characters use multiple UTF-8 bytes, so the system must process bytes rather than individual characters.
2. If bit errors remain after decoding, UTF-8 decoding may fail or produce garbled text.
3. Padding bits must be removed before UTF-8 decoding.

---

## 5.2 Scrambling Module

### Function

The scrambling module applies a reversible XOR operation to the payload bits. This prevents long runs of 0 or 1 and makes the transmitted bitstream more random.

### Algorithm

A pseudo-random PN sequence is generated using the command-line random seed. The payload bits are scrambled by XOR:

```text
scrambled_bits = payload_bits XOR pn_bits
```

At the receiver, the same PN sequence is regenerated using the same seed:

```text
payload_bits = scrambled_bits XOR pn_bits
```

Because XOR is self-inverse, the same operation can be used for scrambling and descrambling.

### Key Parameters

| Parameter | Value |
|---|---|
| Scrambling method | PN XOR scrambling |
| PN length | Same as payload bit length |
| Seed | Command-line `--seed` |

### Risks

1. The transmitter and receiver must use the same seed and same PN generation rule.
2. The PN sequence length must match the original payload length after channel decoding.

---

## 5.3 Channel Coding Module

### Function

The channel coding module adds redundancy to improve resistance to noise.

### Baseline Choice

The baseline system uses a 3-times repetition code.

### Encoder

Each bit is repeated 3 times:

```text
0 -> 000
1 -> 111
```

### Decoder

The receiver performs majority voting every 3 bits:

```text
000 -> 0
001 -> 0
010 -> 0
100 -> 0
011 -> 1
101 -> 1
110 -> 1
111 -> 1
```

### Coding Rate

The coding rate is:

```text
R = 1 / 3
```

### Reason for Selection

The repetition code is selected for the baseline implementation because:

1. It is simple and reliable.
2. It is easy to test and debug.
3. It provides basic error correction capability.
4. It is easy to explain in the final defense.

### Risks

1. The coding efficiency is low because the number of payload bits becomes three times larger.
2. The repetition code can correct only limited errors in each 3-bit group.
3. At very low SNR, multiple errors in the same group may cause decoding failure.

---

## 5.4 Frame Structure Module

### Function

The frame structure module packs the transmitted data into a frame that supports synchronization, length recognition, payload extraction, and error detection.

### Frame Format

The baseline frame format is:

```text
[preamble][length][encoded_payload][checksum]
```

| Field | Length | Description |
|---|---:|---|
| preamble | 128 bits | Known synchronization sequence |
| length | 32 bits | Original payload bit length before scrambling |
| encoded_payload | 3 × payload_bits | Scrambled and repetition-coded payload |
| checksum | 32 bits | CRC32 or checksum of original payload bytes |

### Field Details

#### Preamble

The preamble is a fixed known bit sequence. It is converted to QPSK symbols and used by the receiver for frame start detection.

The preamble length is selected as 128 bits, corresponding to 64 QPSK symbols. A longer preamble gives a sharper correlation peak and improves synchronization reliability.

#### Length Field

The length field stores the number of original payload bits after source encoding and before scrambling.

This field is important because QPSK modulation may add padding bits at the end of the frame. The receiver uses the length value to remove padding and recover the exact original UTF-8 bitstream.

#### Encoded Payload

The payload field contains the scrambled and channel-coded payload bits.

For the baseline repetition code:

```text
encoded_payload_length = 3 × original_payload_bit_length
```

#### Checksum Field

The checksum field stores a CRC32 value computed from the original payload bytes before scrambling. At the receiver, the decoded and descrambled payload is converted back to bytes and checked again.

The checksum result is recorded as `checksum_pass` in `metrics.json`.

### Frame Parsing at Receiver

After QPSK demodulation, the receiver:

1. Reads the 32-bit length field.
2. Computes the expected encoded payload length.
3. Extracts the encoded payload.
4. Extracts the 32-bit checksum field.
5. Decodes the payload using repetition decoding.
6. Descrambles the decoded payload.
7. Truncates the result according to the original payload bit length.
8. Verifies the checksum.

### Risks

1. If the length field is decoded incorrectly, payload extraction may fail.
2. If synchronization is wrong, all subsequent fields may be shifted.
3. If low SNR causes many bit errors, the checksum may fail.

---

## 5.5 QPSK Modulation Module

### Function

The modulation module maps binary bits to complex QPSK symbols.

### Required Gray-Coded QPSK Mapping

The baseline system uses the required Gray-coded QPSK mapping:

```text
00 -> (1 + j) / sqrt(2)
01 -> (-1 + j) / sqrt(2)
11 -> (-1 - j) / sqrt(2)
10 -> (1 - j) / sqrt(2)
```

Each QPSK symbol carries 2 bits.

### Normalization

All QPSK symbols are normalized by `sqrt(2)`, so the average symbol power is approximately 1:

```text
E[|s|^2] = 1
```

### Padding

If the number of bits entering QPSK modulation is not a multiple of 2, one `0` bit is appended at the end of the frame.

At the receiver, padding is removed according to the payload length field and frame structure.

### Demodulation

The receiver uses hard-decision nearest-neighbor demodulation. The sign of the real and imaginary parts determines the quadrant, and the corresponding bit pair is recovered according to the same Gray mapping.

### Risks

1. The mapping must be exactly consistent between transmitter and receiver.
2. The QPSK padding bit must not be interpreted as payload.
3. At low SNR, symbols near decision boundaries may be demodulated incorrectly.

---

## 5.6 Channel Module

### Function

The baseline channel module simulates an AWGN channel.

### AWGN Model

The received signal is:

```text
r[k] = s[k] + n[k]
```

where:

- `s[k]` is the transmitted QPSK symbol.
- `n[k]` is complex Gaussian noise.

### SNR Definition

The baseline SNR is defined as:

```text
SNR = average received modulation symbol power / average complex Gaussian noise power
```

In dB:

```text
SNR_dB = 10 × log10(signal_power / noise_power)
```

For a target SNR value:

```text
noise_power = signal_power / 10^(SNR_dB / 10)
```

The complex noise is generated as:

```text
n = sqrt(noise_power / 2) × (randn + j × randn)
```

so that:

```text
E[|n|^2] = noise_power
```

### Random Prefix Offset

To test synchronization, the channel module may insert a random number of QPSK symbols before the valid frame:

```text
prefix_offset_symbols ∈ [0, 128]
```

The receiver must detect the actual frame start by correlation with the known preamble.

### Key Parameters

| Parameter | Value |
|---|---|
| Baseline channel | AWGN |
| SNR input | `--snr` |
| Random seed | `--seed` |
| Prefix offset range | 0 to 128 QPSK symbols |

### Risks

1. At low SNR, the QPSK constellation becomes blurred.
2. Synchronization may fail if the preamble correlation peak is not clear.
3. Fixed seed must make the random noise and prefix offset reproducible.

---

## 5.7 Synchronization Module

### Function

The synchronization module detects the start index of the received frame.

### Algorithm

1. Generate the known preamble bit sequence.
2. Modulate the preamble bits into QPSK symbols.
3. Slide the known preamble symbols over the received symbol sequence.
4. Compute the correlation value at each possible position.
5. Select the position with the maximum correlation peak.

The estimated frame start index is:

```text
sync_start_index = argmax(correlation)
```

### Output

The synchronization module outputs:

1. Estimated frame start index.
2. Correlation sequence.
3. Peak value.
4. Optional synchronization confidence value.

### Requirement

Under AWGN channel and SNR >= 12 dB, the frame start detection error should be no more than 1 QPSK symbol.

### Risks

1. Low SNR may reduce the correlation peak.
2. A short preamble may cause false peaks.
3. If QPSK mapping of the preamble is inconsistent, synchronization will fail.

---

## 5.8 Receiver Processing Module

After synchronization, the receiver performs the inverse processing chain:

```text
synchronized symbols
-> QPSK demodulation
-> frame parsing
-> repetition decoding
-> descrambling
-> source decoding
-> received.txt
```

The receiver also computes metrics by comparing the original payload and recovered payload.

If decoding or checksum verification fails, the receiver should still:

1. Write a best-effort `received.txt` if possible.
2. Generate `metrics.json`.
3. Record `checksum_pass = false`.
4. Record failure reason in metrics.

---

## 5.9 Metrics Module

The system must generate `results/metrics.json`.

### Required Fields

At minimum, the metrics file should include:

```json
{
  "snr_db": 12,
  "seed": 2026,
  "modulation": "qpsk",
  "channel": "awgn",
  "payload_bits": 2400,
  "ber": 0.0,
  "fer": 0.0,
  "text_match_rate": 1.0,
  "checksum_pass": true,
  "sync_start_index": 25
}
```

### Additional Recommended Fields

```json
{
  "coding": "repetition-3",
  "scrambling": "pn-xor",
  "qpsk_mapping": "gray",
  "preamble_bits": 128,
  "prefix_offset_symbols": 25,
  "crc_expected": "0x00000000",
  "crc_received": "0x00000000",
  "sync_peak_value": 0.0,
  "sync_error_symbols": 0,
  "failure_reason": null
}
```

### BER Definition

The BER is calculated by comparing the original payload bits and recovered payload bits after channel decoding and descrambling:

```text
BER = number of wrong payload bits / total payload bits
```

### FER Definition

Because the baseline system uses one frame per file:

```text
FER = 0 if checksum passes and text matches
FER = 1 otherwise
```

### Text Match Rate

The text match rate is:

```text
text_match_rate = 1.0 if received text exactly equals input text
```

If the text is not exactly equal, a character-level similarity ratio can be reported.

---

## 5.10 Plot Module

The system should generate at least two plots from the following three. The baseline implementation will generate all three if possible.

### 1. QPSK Constellation Plot

File name:

```text
results/constellation.png
```

Purpose:

- Show the received QPSK symbols after AWGN channel.
- Help explain how noise affects symbol decisions.

### 2. BER-SNR Curve

File name:

```text
results/ber_curve.png
```

Purpose:

- Show BER performance under different SNR values.
- Recommended SNR points:

```text
0, 2, 4, 6, 8, 10, 12, 14, 16 dB
```

### 3. Synchronization Peak Plot

File name:

```text
results/sync_peak.png
```

Purpose:

- Show the preamble correlation curve.
- Verify that the detected frame start corresponds to the strongest correlation peak.

---

## 6. Command-Line Interface

The baseline command is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

### Required Arguments

| Argument | Description |
|---|---|
| `--input` | Input text file path |
| `--output` | Output received text file path |
| `--snr` | SNR in dB |
| `--seed` | Random seed |
| `--mod` | Modulation type, baseline supports `qpsk` |
| `--channel` | Channel type, baseline supports `awgn` |

### Optional Arguments

The implementation may also support:

| Argument | Description |
|---|---|
| `--no-plots` | Disable plot generation for fast tests |
| `--snr-list` | SNR list for BER curve generation |
| `--prefix-offset` | Fixed prefix offset for debugging |
| `--results-dir` | Output directory |

---

## 7. End-to-End Processing Procedure

## 7.1 Transmitter Procedure

1. Read input text file.
2. Convert UTF-8 bytes to payload bits.
3. Generate PN sequence using seed.
4. Scramble payload bits by XOR.
5. Apply 3-times repetition channel coding.
6. Compute CRC32 from original payload bytes.
7. Build frame with preamble, length, encoded payload, and checksum.
8. Add QPSK padding if needed.
9. Modulate bits to QPSK symbols.
10. Pass QPSK symbols through AWGN channel with random prefix offset.

## 7.2 Receiver Procedure

1. Use preamble correlation to detect frame start.
2. Remove prefix and align received frame.
3. QPSK demodulate synchronized symbols to bits.
4. Parse length field.
5. Extract encoded payload and checksum.
6. Decode the payload using majority voting.
7. Descramble the decoded payload using the same PN sequence.
8. Truncate the recovered bitstream according to the length field.
9. Convert recovered bits to UTF-8 text.
10. Save text to `results/received.txt`.
11. Verify checksum.
12. Compute BER, FER, and text match rate.
13. Save `results/metrics.json`.
14. Generate visualization plots.

---

## 8. Parameter Summary

| Parameter | Baseline Value |
|---|---|
| Text encoding | UTF-8 |
| Scrambling | PN XOR |
| Channel coding | Repetition code, repeat factor = 3 |
| Frame preamble | 128 bits |
| Length field | 32 bits |
| Checksum | CRC32, 32 bits |
| Modulation | Gray-coded QPSK |
| Symbol normalization | Average symbol power = 1 |
| Channel | AWGN |
| SNR definition | Symbol power / complex noise power |
| Prefix offset | 0 to 128 QPSK symbols |
| Required high-SNR condition | SNR >= 12 dB |
| Required output | Exact text recovery under public baseline condition |

---

## 9. Testing Strategy Overview

The implementation will be developed using module-level tests and end-to-end tests.

Planned tests include:

1. Source encoding and decoding round-trip test.
2. Scrambler reversibility test.
3. Repetition encoder and decoder test.
4. Frame build and parse test.
5. QPSK mapping and demapping test.
6. AWGN reproducibility test with fixed seed.
7. Synchronization test with random prefix offset.
8. End-to-end no-noise test.
9. End-to-end SNR = 12 dB test.
10. Low-SNR robustness test.
11. Output file and metrics generation test.
12. Plot generation test.

Detailed test cases are described in `TEST_PLAN.md`.

---

## 10. Expected Results

Under the public baseline condition:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Expected results:

1. Program exits normally.
2. `results/received.txt` is generated.
3. `results/received.txt` exactly matches `Test.txt`.
4. `results/metrics.json` is generated.
5. `checksum_pass` is `true`.
6. `text_match_rate` is `1.0`.
7. BER is expected to be `0.0` or very close to `0.0`.
8. FER is expected to be `0.0`.
9. At least two plots are generated.

---

## 11. Known Risks and Mitigation

| Risk | Possible Cause | Mitigation |
|---|---|---|
| UTF-8 decoding error | Residual bit errors | Use channel coding, checksum, and safe decode fallback |
| Wrong frame start | Weak correlation peak | Use 128-bit preamble and normalized correlation |
| Wrong length parsing | Header bit errors | Test at SNR >= 12 dB and optionally protect length field in later revision |
| QPSK mapping mismatch | Different mapping in modulator and demodulator | Define one shared mapping table |
| Padding error | QPSK bit count not divisible by 2 | Store original payload length and remove padding |
| Hidden test failure | Hard-coded length or input content | Use dynamic length and general file reading |
| Low-SNR failure | Excessive symbol errors | Do not crash; record checksum failure and BER |
| Plot generation failure | Missing results directory | Create results directory automatically |

---

## 12. Possible Extension Modules

If the baseline system is stable, the following extension modules may be added for Level 3:

1. Rayleigh fading channel.
2. Simple one-tap equalization.
3. BPSK and 16-QAM comparison.
4. Convolutional code with Viterbi decoding.
5. Adaptive modulation comparison.
6. Simple graphical user interface.

The preferred extension is Rayleigh fading channel because it is closely related to wireless communication and is easier to explain with constellation and BER comparison.

## 12.1 Level 3 Extension: Rayleigh Fading and One-Tap Equalization

The Level 3 implementation adds an optional Rayleigh fading channel while preserving the required AWGN baseline command.

The new Rayleigh command is:

```bash
python main.py --input Test.txt --output results/received_rayleigh.txt --snr 12 --seed 2026 --mod qpsk --channel rayleigh
```

### Rayleigh Channel Model

For each QPSK symbol, a complex flat Rayleigh fading coefficient is generated:

```text
h = (randn + j * randn) / sqrt(2)
```

The received signal is:

```text
r = h * s + n
```

where `s` is the transmitted QPSK symbol and `n` is complex AWGN. The random seed controls both fading and noise generation so that the experiment is reproducible.

### One-Tap Equalization

In the simulation, the receiver is allowed to know the fading coefficient `h`. The equalized symbol is:

```text
r_eq = r / h
```

An epsilon value is used to avoid division by zero:

```text
epsilon = 1e-12
```

For `--channel rayleigh`, one-tap equalization is enabled by default before synchronization and demodulation. For `--channel awgn`, Rayleigh fading and equalization are not used.

The metrics file records the extension fields:

```text
equalization = "one-tap"
fading_model = "flat_rayleigh"
rayleigh_enabled = true
channel_estimation = "known_h_simulation"
```

---

## 13. Design Revision Record

This section should be updated after mock testing.

| Version | Change | Reason |
|---|---|---|
| v0.1 | Initial design using PN scrambling, repetition coding, QPSK, AWGN, and preamble synchronization | Satisfy baseline PRD requirements |
| v0.2 | To be updated after mock tests | To be filled in `MOCK_TEST_REPORT.md` |
| v0.3 | Implemented the full end-to-end baseline pipeline. The required command generated received.txt, metrics.json, and three plots. At SNR = 12 dB, AWGN, seed = 2026, received.txt matched Test.txt at byte level with BER = 0.0, FER = 0.0, text_match_rate = 1.0, and checksum_pass = true. | Verified that the baseline design satisfies the main public acceptance condition. |
| v0.4 | Added Level 3 Rayleigh fading channel extension with simple one-tap equalization and comparison experiment support. The baseline AWGN command remains unchanged and continues to recover Test.txt exactly under SNR = 12 dB. | Added an advanced wireless channel module while preserving the required baseline system. |
