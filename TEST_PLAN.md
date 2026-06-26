# TEST_PLAN.md

# Wireless Final Project Test Plan

## 1. Purpose

This document defines the test plan for the wireless communication file transmission baseband simulation system.

The test plan verifies that the system can:

1. Read `Test.txt` correctly.
2. Convert UTF-8 text to bits and recover it.
3. Perform reversible scrambling and descrambling.
4. Perform channel coding and decoding.
5. Build and parse frames correctly.
6. Perform Gray-coded QPSK modulation and demodulation.
7. Simulate an AWGN channel with configurable SNR and fixed seed.
8. Detect frame start using preamble-based synchronization.
9. Recover `results/received.txt`.
10. Generate `results/metrics.json`.
11. Generate required plots.
12. Pass public tests and avoid hard-coded behavior.

The baseline validation command is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

---

## 2. Test Environment

Recommended environment:

| Item | Requirement |
|---|---|
| Language | Python 3.9 or later |
| Required packages | numpy, matplotlib, pytest |
| Optional packages | scipy |
| OS | Windows, Linux, or macOS |
| Entry point | `main.py` |
| Test command | `pytest public_tests -q` or `pytest tests -q` |

The project should not depend on absolute local paths. All file paths should be passed through command-line arguments or relative project paths.

---

## 3. Test Scope

## 3.1 In Scope

The following parts are included in the test scope:

1. Source encoding and decoding.
2. Scrambling and descrambling.
3. Channel coding and decoding.
4. Frame construction and parsing.
5. QPSK modulation and demodulation.
6. AWGN channel.
7. Random seed reproducibility.
8. Preamble synchronization.
9. End-to-end file recovery.
10. Metrics and plot generation.
11. Low-SNR robustness.
12. Invalid input handling.
13. Anti-hardcoding checks.

## 3.2 Out of Scope for Baseline

The following parts are not required for the baseline system, but may be tested if implemented as extensions:

1. Rayleigh fading channel.
2. Rician fading channel.
3. OFDM.
4. Diversity combining.
5. Equalization.
6. 16-QAM.
7. Graphical user interface.

---

## 4. Test Data

## 4.1 Basic Input Text

Use the teacher-provided `Test.txt`.

Expected behavior:

- The program reads the file as UTF-8.
- The recovered `results/received.txt` exactly matches `Test.txt` under SNR >= 12 dB AWGN condition.

## 4.2 Additional Local Test Texts

To avoid hard-coded behavior, additional local tests should be created:

### Case A: Short English Text

```text
Hello wireless communication.
```

### Case B: Short Chinese Text

```text
无线通信技术期末项目测试。
```

### Case C: Mixed Text

```text
QPSK 调制 + AWGN 信道 + UTF-8 文本传输 test 2026.
```

### Case D: Long Text

A longer text with more than 500 UTF-8 characters.

### Case E: Empty or Very Short Text

```text
A
```

Expected behavior:

- The system should handle variable input length.
- The system should not assume the public `Test.txt` content or length.

---

## 5. Unit Test Plan

## TC-01 Source Encoding Round-Trip

### Purpose

Verify that UTF-8 text can be converted to bits and recovered correctly.

### Steps

1. Prepare a Chinese and English mixed text.
2. Convert text to UTF-8 bytes.
3. Convert bytes to bits.
4. Convert bits back to bytes.
5. Decode bytes as UTF-8 text.

### Expected Result

The recovered text is exactly the same as the original text.

### Pass Criteria

```text
decoded_text == original_text
```

---

## TC-02 Source Encoding Payload Length

### Purpose

Verify that payload bit length is calculated correctly.

### Steps

1. Read input text as UTF-8 bytes.
2. Compute bit length as `len(payload_bytes) * 8`.
3. Compare it with the length stored in the frame length field.

### Expected Result

The length field equals the original payload bit length before scrambling.

### Pass Criteria

```text
length_field == len(payload_bytes) * 8
```

---

## TC-03 Scrambler Reversibility

### Purpose

Verify that PN XOR scrambling is reversible.

### Steps

1. Generate a random bitstream.
2. Generate PN sequence using a fixed seed.
3. Scramble the bitstream by XOR.
4. Descramble using the same seed.
5. Compare the result with the original bitstream.

### Expected Result

The descrambled bitstream equals the original bitstream.

### Pass Criteria

```text
descrambled_bits == original_bits
```

---

## TC-04 Scrambler Seed Reproducibility

### Purpose

Verify that the same seed generates the same PN sequence.

### Steps

1. Generate PN sequence with seed 2026.
2. Generate PN sequence again with seed 2026.
3. Generate PN sequence with a different seed.
4. Compare the sequences.

### Expected Result

The two sequences generated with the same seed are identical. The sequence generated with a different seed is different.

### Pass Criteria

```text
pn(seed=2026) == pn(seed=2026)
pn(seed=2026) != pn(seed=2027)
```

---

## TC-05 Repetition Encoder

### Purpose

Verify that the repetition encoder repeats every bit 3 times.

### Steps

1. Input bits: `1010`.
2. Apply repetition encoding.
3. Compare with expected result.

### Expected Result

```text
1010 -> 111000111000
```

### Pass Criteria

Encoded bits match expected bits.

---

## TC-06 Repetition Decoder Majority Voting

### Purpose

Verify that the repetition decoder performs majority voting correctly.

### Steps

1. Input encoded groups:
   - `111`
   - `110`
   - `100`
   - `000`
2. Decode each group.

### Expected Result

```text
111 -> 1
110 -> 1
100 -> 0
000 -> 0
```

### Pass Criteria

Decoded bits match expected bits.

---

## TC-07 Frame Build and Parse

### Purpose

Verify that frame construction and parsing are consistent.

### Steps

1. Prepare a payload bitstream.
2. Scramble and encode the payload.
3. Build a frame with preamble, length, encoded payload, and checksum.
4. Parse the frame.
5. Verify all fields.

### Expected Result

1. Preamble matches the known sequence.
2. Length field equals original payload bit length.
3. Encoded payload length equals `3 × payload_bits`.
4. Checksum matches the original payload bytes.

### Pass Criteria

All parsed fields are correct.

---

## TC-08 Checksum Verification

### Purpose

Verify that CRC32 or checksum can detect payload errors.

### Steps

1. Compute checksum for original payload bytes.
2. Flip one bit in the recovered payload.
3. Compute checksum again.
4. Compare with original checksum.

### Expected Result

Checksum verification fails after bit flipping.

### Pass Criteria

```text
checksum_pass == false
```

---

## TC-09 QPSK Mapping

### Purpose

Verify that QPSK uses the required Gray mapping.

### Test Mapping

```text
00 -> (1 + j) / sqrt(2)
01 -> (-1 + j) / sqrt(2)
11 -> (-1 - j) / sqrt(2)
10 -> (1 - j) / sqrt(2)
```

### Steps

1. Input bit pairs: `00`, `01`, `11`, `10`.
2. Modulate them to QPSK symbols.
3. Compare with expected complex values.

### Expected Result

The mapping exactly follows the required Gray-coded QPSK table.

### Pass Criteria

All mapped symbols match expected values within floating-point tolerance.

---

## TC-10 QPSK Demodulation Without Noise

### Purpose

Verify that QPSK demodulation can recover bits without noise.

### Steps

1. Generate a random bitstream.
2. Apply QPSK modulation.
3. Apply QPSK demodulation without channel noise.
4. Compare recovered bits with original bits.

### Expected Result

Recovered bits exactly match original bits, except any intentionally added QPSK padding bit.

### Pass Criteria

```text
demod_bits[:original_length] == original_bits
```

---

## TC-11 QPSK Padding

### Purpose

Verify that odd-length bitstreams are padded correctly.

### Steps

1. Generate a bitstream with odd length.
2. Apply QPSK modulation.
3. Check that one padding bit is added.
4. Demodulate the symbols.
5. Remove padding according to original length.

### Expected Result

The final recovered bitstream equals the original bitstream.

### Pass Criteria

```text
recovered_bits == original_bits
```

---

## TC-12 AWGN Reproducibility

### Purpose

Verify that AWGN output is reproducible under a fixed seed.

### Steps

1. Generate QPSK symbols.
2. Pass them through AWGN channel with seed 2026.
3. Repeat the same operation with seed 2026.
4. Compare the two received symbol arrays.

### Expected Result

The two outputs are identical or numerically equal within floating-point tolerance.

### Pass Criteria

```text
np.allclose(rx1, rx2) == true
```

---

## TC-13 AWGN SNR Sanity Check

### Purpose

Verify that the generated noise roughly matches the target SNR.

### Steps

1. Generate normalized QPSK symbols.
2. Add AWGN noise at SNR = 12 dB.
3. Estimate signal power and noise power.
4. Compute empirical SNR.

### Expected Result

The empirical SNR should be close to the target SNR.

### Pass Criteria

The empirical SNR error should be within a reasonable tolerance, such as 1 dB for a sufficiently long sequence.

---

## TC-14 Synchronization Without Noise

### Purpose

Verify that the synchronization module finds the correct frame start without noise.

### Steps

1. Generate a complete QPSK frame.
2. Add a known prefix offset of 25 QPSK symbols.
3. Run preamble correlation synchronization.
4. Compare detected start index with 25.

### Expected Result

The detected start index equals the true prefix offset.

### Pass Criteria

```text
sync_start_index == true_offset
```

---

## TC-15 Synchronization With AWGN

### Purpose

Verify that synchronization works under the public baseline SNR.

### Steps

1. Generate a complete QPSK frame.
2. Add random prefix offset between 0 and 128 symbols.
3. Add AWGN with SNR = 12 dB.
4. Run synchronization.
5. Compare detected start index with true offset.

### Expected Result

The synchronization error should not exceed 1 QPSK symbol.

### Pass Criteria

```text
abs(sync_start_index - true_offset) <= 1
```

---

## 6. Integration Test Plan

## IT-01 End-to-End Noiseless Transmission

### Purpose

Verify the full communication chain without channel noise.

### Command

```bash
python main.py --input Test.txt --output results/received.txt --snr 100 --seed 2026 --mod qpsk --channel awgn
```

### Expected Result

1. Program exits normally.
2. `results/received.txt` is generated.
3. `received.txt` exactly matches `Test.txt`.
4. `checksum_pass` is `true`.
5. BER is `0.0`.
6. FER is `0.0`.

### Pass Criteria

```text
received.txt == Test.txt
```

---

## IT-02 Public Baseline End-to-End Test

### Purpose

Verify the required public baseline condition.

### Command

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

### Expected Result

1. Program exits normally.
2. `results/received.txt` is generated.
3. `results/metrics.json` is generated.
4. `received.txt` exactly matches `Test.txt`.
5. `checksum_pass` is `true`.
6. `text_match_rate` is `1.0`.
7. BER is `0.0` or very close to `0.0`.
8. FER is `0.0`.
9. At least two plots are generated.

### Pass Criteria

```text
received.txt == Test.txt
```

---

## IT-03 Different Seed Test

### Purpose

Verify that the program works under different random seeds.

### Commands

```bash
python main.py --input Test.txt --output results/received_seed1.txt --snr 12 --seed 1 --mod qpsk --channel awgn
python main.py --input Test.txt --output results/received_seed2.txt --snr 12 --seed 2027 --mod qpsk --channel awgn
```

### Expected Result

Both output files should match `Test.txt`.

### Pass Criteria

```text
received_seed1.txt == Test.txt
received_seed2.txt == Test.txt
```

---

## IT-04 Variable Input Content Test

### Purpose

Verify that the program does not hard-code the public `Test.txt`.

### Steps

1. Create a new input file with different Chinese and English mixed content.
2. Run the baseline command using this new file.
3. Compare the output with the new input.

### Command

```bash
python main.py --input local_test.txt --output results/local_received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

### Expected Result

The output matches the new input file.

### Pass Criteria

```text
local_received.txt == local_test.txt
```

---

## IT-05 Variable Length Test

### Purpose

Verify that the program supports different input lengths.

### Steps

1. Test a very short text file.
2. Test a medium text file.
3. Test a long text file.
4. Run the full system for each file.

### Expected Result

All files are recovered correctly at SNR = 12 dB.

### Pass Criteria

All output files match their corresponding input files.

---

## IT-06 Low-SNR Robustness Test

### Purpose

Verify that the system does not crash at low SNR.

### Command

```bash
python main.py --input Test.txt --output results/received_low_snr.txt --snr 0 --seed 2026 --mod qpsk --channel awgn
```

### Expected Result

The program should:

1. Exit normally.
2. Generate `received_low_snr.txt` if decoding is possible.
3. Generate `metrics.json`.
4. Record BER, FER, text match rate, and checksum result.
5. Record failure reason if recovery fails.

### Pass Criteria

The program does not crash and produces metrics.

---

## IT-07 Output File Structure Test

### Purpose

Verify that required output files are generated.

### Steps

1. Run the public baseline command.
2. Check the `results/` directory.

### Expected Required Files

```text
results/received.txt
results/metrics.json
```

### Expected Plot Files

At least two of the following:

```text
results/constellation.png
results/ber_curve.png
results/sync_peak.png
```

### Pass Criteria

Required files exist and are non-empty.

---

## IT-08 Metrics JSON Field Test

### Purpose

Verify that `metrics.json` contains all required fields.

### Required Fields

```text
snr_db
seed
modulation
channel
payload_bits
ber
fer
text_match_rate
checksum_pass
sync_start_index
```

### Steps

1. Run the public baseline command.
2. Load `results/metrics.json`.
3. Check required fields and data types.

### Expected Result

All required fields exist.

### Pass Criteria

No required field is missing.

---

## IT-09 Plot Generation Test

### Purpose

Verify that visualization files are generated correctly.

### Steps

1. Run the public baseline command.
2. Check plot files in the `results/` directory.
3. Verify that each generated image file is non-empty.

### Expected Result

At least two valid image files are generated.

### Pass Criteria

At least two of the following files exist and are non-empty:

```text
constellation.png
ber_curve.png
sync_peak.png
```

---

## 7. Robustness Test Plan

## RT-01 Missing Input File

### Purpose

Verify that the program handles missing input files properly.

### Command

```bash
python main.py --input missing.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

### Expected Result

The program should print a clear error message and exit gracefully.

### Pass Criteria

No unclear traceback should be shown to the user in normal mode.

---

## RT-02 Invalid Modulation

### Purpose

Verify that unsupported modulation is rejected.

### Command

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod unknown --channel awgn
```

### Expected Result

The program should report that the modulation type is unsupported.

### Pass Criteria

The program exits with a meaningful error message.

---

## RT-03 Invalid Channel

### Purpose

Verify that unsupported channel type is rejected.

### Command

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel unknown
```

### Expected Result

The program should report that the channel type is unsupported.

### Pass Criteria

The program exits with a meaningful error message.

---

## RT-04 Very Low SNR

### Purpose

Verify that the system records failure metrics instead of crashing.

### Command

```bash
python main.py --input Test.txt --output results/received_very_low.txt --snr -5 --seed 2026 --mod qpsk --channel awgn
```

### Expected Result

The output text may not match the input text, but the program should still generate metrics and record checksum failure if applicable.

### Pass Criteria

Program exits normally and writes metrics.

---

## 8. Mock Test Plan

Before writing the final system code, the following mock tests should be performed to validate design feasibility.

| Mock Test ID | Test Target | Expected Finding |
|---|---|---|
| MOCK-01 | Source encoding and decoding | UTF-8 text can be recovered exactly |
| MOCK-02 | Frame build and parse | Length and checksum fields can be parsed correctly |
| MOCK-03 | QPSK without noise | Modulation and demodulation are lossless |
| MOCK-04 | AWGN with fixed seed | Channel output is reproducible |
| MOCK-05 | Synchronization with fixed offset | Preamble correlation detects frame start |
| MOCK-06 | End-to-end at SNR = 12 dB | `received.txt` matches `Test.txt` |
| MOCK-07 | Low-SNR run | System outputs metrics instead of crashing |

The actual mock test results and design changes should be recorded in `MOCK_TEST_REPORT.md`.

---

## 9. Public Test Preparation

Before submitting the project, run:

```bash
pytest public_tests -q
```

If the teacher template uses a different public test directory, run the command specified in the repository README or GitHub Actions workflow.

The following checks should be completed before pushing:

1. `main.py` exists in the repository root.
2. The command-line interface matches the PRD.
3. No absolute local path is used.
4. `results/received.txt` can be generated.
5. `results/metrics.json` can be generated.
6. At least two plots can be generated.
7. No public input content is hard-coded.
8. The implementation supports different input text files.
9. The implementation supports different seeds.
10. The project can run from a clean clone.

---

## 9.1 Level 3 Extension Test Plan

The Level 3 extension adds Rayleigh fading, simple one-tap equalization, and AWGN-vs-Rayleigh comparison plots. These tests must not change the required AWGN baseline behavior.

### L3-01 Rayleigh Channel Reproducibility Test

Purpose:

Verify that Rayleigh fading is reproducible under a fixed seed.

Steps:

1. Generate a fixed QPSK symbol sequence.
2. Run the Rayleigh fading channel with `snr_db = 12` and `seed = 2026`.
3. Repeat the same channel call with the same seed.
4. Compare both the received symbols and fading coefficients.

Expected result:

```text
rx(seed=2026) == rx(seed=2026)
h(seed=2026) == h(seed=2026)
```

### L3-02 One-Tap Equalization Test

Purpose:

Verify that known-channel one-tap equalization can invert flat fading in a noiseless sanity test.

Steps:

1. Generate QPSK symbols.
2. Multiply them by known nonzero fading coefficients `h`.
3. Apply `r_eq = r / h`.
4. Demodulate the equalized symbols.

Expected result:

```text
demodulated_bits == original_bits
```

### L3-03 AWGN vs Rayleigh Comparison Test

Purpose:

Verify that the project can generate comparison results for AWGN and Rayleigh + one-tap equalization.

Steps:

1. Run the baseline AWGN command.
2. Run the Rayleigh command.
3. Check that `metrics.json` records the correct channel mode and extension fields.
4. Check that `results/ber_curve_compare.png` is generated.

Expected result:

The comparison plot exists and the metrics file includes:

```text
channel = "rayleigh"
equalization = "one-tap"
fading_model = "flat_rayleigh"
rayleigh_enabled = true
```

### L3-04 Rayleigh CLI Smoke Test

Purpose:

Verify that the new Rayleigh command exits normally and writes output artifacts without hard-coding the result.

Command:

```bash
python main.py --input Test.txt --output results/received_rayleigh.txt --snr 12 --seed 2026 --mod qpsk --channel rayleigh
```

Expected result:

The program exits normally. If the Rayleigh channel leaves residual bit errors, the program should not force a correct output. It should record BER, FER, `checksum_pass`, `text_match_rate`, and `failure_reason` in `metrics.json`.

---

## 10. Acceptance Criteria

The baseline project is considered acceptable if all of the following are satisfied:

1. The program runs with the required command.
2. The program exits normally under SNR = 12 dB AWGN.
3. `results/received.txt` is generated.
4. `results/received.txt` exactly matches `Test.txt`.
5. `results/metrics.json` is generated.
6. `metrics.json` contains all required fields.
7. `checksum_pass` is `true` under public baseline condition.
8. `text_match_rate` is `1.0` under public baseline condition.
9. At least two required plots are generated.
10. The code is modular and does not hard-code public test content.
11. Low-SNR cases do not crash the program.
12. The test results are summarized in `MOCK_TEST_REPORT.md`.

---

## 11. Test Result Record Template

The following table can be copied into `MOCK_TEST_REPORT.md` after running tests.

| Test ID | Test Name | Command or Method | Expected Result | Actual Result | Pass/Fail | Notes |
|---|---|---|---|---|---|---|
| TC-01 | Source encoding round-trip | Unit test | Exact recovery |  |  |  |
| TC-03 | Scrambler reversibility | Unit test | Exact recovery |  |  |  |
| TC-05 | Repetition encoder | Unit test | Correct repetition |  |  |  |
| TC-07 | Frame build and parse | Unit test | Correct fields |  |  |  |
| TC-09 | QPSK mapping | Unit test | Required Gray mapping |  |  |  |
| TC-12 | AWGN reproducibility | Unit test | Same seed same output |  |  |  |
| TC-15 | Synchronization with AWGN | Unit test | Error <= 1 symbol |  |  |  |
| IT-02 | Public baseline E2E | CLI run | received.txt matches Test.txt |  |  |  |
| IT-06 | Low-SNR robustness | CLI run | No crash, metrics generated |  |  |  |
| IT-08 | Metrics JSON field check | File check | All required fields exist |  |  |  |

---

## 12. Final Submission Checklist

Before creating the Pull Request, check the following items:

```text
[ ] DESIGN.md completed
[ ] TEST_PLAN.md completed
[ ] MOCK_TEST_REPORT.md completed
[ ] AI_LOG.md completed
[ ] main.py completed
[ ] src/ modules completed
[ ] tests/ or public_tests verified
[ ] results/received.txt generated
[ ] results/metrics.json generated
[ ] At least two plots generated
[ ] Required CLI command works
[ ] SNR = 12 dB AWGN exact recovery verified
[ ] Different input text verified
[ ] Different seed verified
[ ] Low-SNR case does not crash
[ ] No hard-coded public test input or output
[ ] Code and document descriptions are consistent
```
