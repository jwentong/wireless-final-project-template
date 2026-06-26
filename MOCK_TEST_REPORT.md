# MOCK_TEST_REPORT.md

# Wireless Final Project Mock Test Report

## 1. Purpose of Mock Testing

This mock test stage was conducted after completing the initial `DESIGN.md` and `TEST_PLAN.md`.

The purpose of this stage is not to complete the final end-to-end wireless file transmission system immediately. Instead, the goal is to verify whether the core module interfaces and baseline technical choices in the design are feasible before implementing the complete system.

The mock tests mainly focus on the following parts:

1. UTF-8 source encoding and decoding.
2. PN XOR scrambling and descrambling.
3. Repetition-3 channel coding and decoding.
4. Frame construction and parsing.
5. Gray-coded QPSK modulation and demodulation.
6. AWGN channel reproducibility with fixed random seed.
7. Preamble-based synchronization using correlation.

The result of this stage is used to decide whether the selected baseline architecture can be used for the next full implementation stage.

---

## 2. Current Stage Scope

## 2.1 Completed in Stage 1

The following project skeleton and modules have beereated:

```text
main.py
src/
  source_codec.py
  scrambler.py
  channel_codec.py
  frame.py
  modulation.py
  channel.py
  synchronization.py
tests/
  test_mock_stage1.py
pytest.ini
```

The current `main.py` provides a command-line placeholder and supports the required arguments:

```text
--input
--output
--snr
--seed
--mod
--channel
```

The `src/` directory contains the initial modular functions needed for the baseline system:

| Module | Current Function |
|---|---|
| `source_codec.py` | UTF-8 text/bytes and bitstream round-trip conversion |
| `scrambler.py` | PN XOR scrambling and descrambling |
| `channel_codec.py` | Repetition-3 channel coding and majority-vote decoding |
| `frame.py` | Frame construction and parsing with preamble, length, payload, and CRC32 |
| `modulation.py` | Gray-coded QPSK modulation and demodulation |
| `channel.py` | AWGN channel and known-prefix helper |
| `synchronization.py` | Preamble-correlation synchronization |

The current `tests/test_mock_stage1.py` contains seven mock tests.

## 2.2 Not Completed in Stage 1

The following parts are not yet implemented in this stage:

1. Complete transmitter-to-receiver end-to-end flow in `main.py`.
2. Generation of final `results/received.txt`.
3. Generation of final `results/metrics.json`.
4. Generation of visualization plots:
   - `constellation.png`
   - `ber_curve.png`
   - `sync_peak.png`
5. Public test validation.
6. Hidden test validation.
7. Low-SNR failure analysis with final metrics.

Therefore, this stage should be regarded as a design feasibility and module-interface verification stage, not as the final system implementation.

---

## 3. Test Environment

The mock tests were run in the local Python development environment.

| Item | Value |
|---|---|
| Operating system | Windows local development environment |
| Project directory | `E:/GithubProjects/wireless-final-project-template` |
| Test framework | pytest |
| Test file | `tests/test_mock_stage1.py` |
| Command | `pytest tests -q` |

The reported test result was:

```text
pytest tests -q
7 passed in 0.24s
```

---

## 4. Mock Test Results

| Test ID | Test Name | Test Target | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| MOCK-01 | Source codec round trip | Verify UTF-8 source encoding and decoding | Text/bytes can be converted to bits and recovered exactly | Passed | Pass |
| MOCK-02 | Scrambler reversibility | Verify PN XOR scrambling and descrambling | Descrambled bits equal original bits | Passed | Pass |
| MOCK-03 | Repetition-3 coding | Verify repetition-3 encoding and majority-vote decoding | Decoded bits match original bits under simple test cases | Passed | Pass |
| MOCK-04 | Frame build and parse | Verify preamble, length, payload, and CRC32 fields | Frame fields can be built and parsed correctly | Passed | Pass |
| MOCK-05 | QPSK mapping and demapping | Verify required Gray-coded QPSK mapping | QPSK mapping follows the PRD mapping and demapping is lossless without noise | Passed | Pass |
| MOCK-06 | AWGN fixed-seed reproducibility | Verify random seed reproducibility in channel simulation | Same seed produces reproducible channel output | Passed | Pass |
| MOCK-07 | Preamble correlation synchronization | Verify synchronization with a known prefix offset | Synchronization can detect the frame start based on preamble correlation | Passed | Pass |

Summary:

```text
Total mock tests: 7
Passed: 7
Failed: 0
Result: Stage-1 mock tests passed
```

---

## 5. Detailed Test Discussion

## 5.1 Source Codec Test

The source codec mock test verifies the most basic file transmission requirement: the input text must be converted into a bitstream and then recovered without loss.

This test is important because the final input file uses UTF-8 encoding and may contain Chinese characters. Chinese characters usually occupy multiple bytes in UTF-8, so the system should process the text at the byte level rather than assuming one character equals one byte.

The mock test result shows that the current source codec interface is feasible for the next stage.

## 5.2 Scrambler Test

The scrambler mock test verifies that the PN XOR scrambling method is reversible.

The transmitter applies:

```text
scrambled_bits = payload_bits XOR pn_bits
```

The receiver applies the same XOR operation with the same PN sequence:

```text
payload_bits = scrambled_bits XOR pn_bits
```

The test result confirms that the selected scrambling method is suitable for the baseline system.

## 5.3 Channel Coding Test

The channel coding mock test verifies the repetition-3 coding scheme.

The transmitter repeats every bit three times:

```text
0 -> 000
1 -> 111
```

The receiver uses majority voting to recover the original bit.

The test result confirms that the encoder and decoder interfaces are correct for basic cases. This coding method is simple but useful for improving the robustness of the baseline system under AWGN noise.

## 5.4 Frame Build and Parse Test

The frame mock test verifies whether the frame format can correctly support payload extraction.

The current baseline frame structure is:

```text
[preamble][length][payload][CRC32]
```

The test verifies the consistency of frame construction and parsing. This is important because the receiver will depend on the preamble for synchronization, the length field for payload recovery, and the CRC32 field for error detection.

The test result confirms that the current frame design is feasible for the next implementation stage.

## 5.5 QPSK Mapping and Demapping Test

The QPSK mock test verifies that the implementation follows the required Gray-coded QPSK mapping:

```text
00 -> (1 + j) / sqrt(2)
01 -> (-1 + j) / sqrt(2)
11 -> (-1 - j) / sqrt(2)
10 -> (1 - j) / sqrt(2)
```

The test checks modulation and demodulation without noise. The successful result shows that the mapping table and hard-decision demapping logic are consistent in the current implementation.

This is a critical baseline requirement because QPSK is the required modulation scheme for the basic system.

## 5.6 AWGN Reproducibility Test

The AWGN mock test verifies that the channel output is reproducible when a fixed random seed is used.

This is important because the project requires fixed seed support for public tests and hidden validation. If the same seed does not produce reproducible output, the teacher's automatic validation may become unstable.

The test result confirms that the current AWGN helper can support reproducible experiments.

## 5.7 Synchronization Test

The synchronization mock test verifies preamble-based frame start detection with a known prefix offset.

The receiver does not assume that the frame starts from the first received symbol. Instead, it uses preamble correlation to find the most likely frame start position.

The successful result shows that the synchronization module can identify the frame start under the current mock condition. This supports the feasibility of the planned synchronization method for the full system.

---

## 6. Problems Found

No failed mock test was found in Stage 1.

However, the following limitations still exist:

1. The current `main.py` is only a command-line placeholder.
2. The complete transmitter-to-receiver flow has not been implemented yet.
3. The program does not yet generate the final `results/received.txt`.
4. The program does not yet generate `results/metrics.json`.
5. The program does not yet generate constellation, BER-SNR, or synchronization plots.
6. The current tests are mock/module-level tests only.
7. The project has not yet been validated with the teacher's public tests.
8. The project has not yet verified exact file recovery under the required command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Therefore, although the Stage-1 mock tests passed, the project is not yet complete and cannot be submitted as the final version.

---

## 7. Design Revisions After Mock Testing

Based on the Stage-1 mock test results, the original baseline architecture is kept.

The following design choices are confirmed:

| Design Item | Decision After Mock Testing | Reason |
|---|---|---|
| Source encoding | Keep UTF-8 byte-to-bit conversion | Mock round-trip test passed |
| Scrambling | Keep PN XOR scrambling | Reversibility test passed |
| Channel coding | Keep repetition-3 coding | Encoding and majority-vote decoding test passed |
| Frame structure | Keep preamble + length + payload + CRC32 | Build/parse test passed |
| Modulation | Keep required Gray-coded QPSK | Mapping/demapping test passed |
| Channel | Keep AWGN with fixed seed support | Reproducibility test passed |
| Synchronization | Keep preamble correlation | Known-offset synchronization test passed |

The following revisions are planned for the next stage:

1. Replace the placeholder `main.py` with a complete end-to-end system.
2. Connect all existing modules into one transmitter-to-receiver chain.
3. Add final file output generation:
   - `results/received.txt`
4. Add metrics output:
   - `results/metrics.json`
5. Add visualization output:
   - `results/constellation.png`
   - `results/ber_curve.png`
   - `results/sync_peak.png`
6. Add full end-to-end tests under SNR = 12 dB AWGN.
7. Add low-SNR robustness handling so the program does not crash when recovery fails.
8. Run the teacher's public tests after the complete system is implemented.

---

## 8. Next Implementation Plan

The next stage is the full baseline system implementation.

The full system should execute the following chain:

```text
Test.txt
-> Source Encode
-> PN XOR Scramble
-> Repetition-3 Channel Encode
-> Frame Build
-> QPSK Modulate
-> AWGN Channel with Random Prefix
-> Preamble Synchronization
-> QPSK Demodulate
-> Frame Parse
-> Repetition-3 Channel Decode
-> PN XOR Descramble
-> Source Decode
-> results/received.txt
-> results/metrics.json and plots
```

The next target command is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Expected result for the next stage:

1. The program exits normally.
2. `results/received.txt` is generated.
3. `results/received.txt` exactly matches `Test.txt` under SNR = 12 dB AWGN.
4. `results/metrics.json` is generated.
5. `checksum_pass` is `true`.
6. `text_match_rate` is `1.0`.
7. BER is `0.0` or close to `0.0`.
8. FER is `0.0`.
9. At least two required plots are generated.

---

## 9. Conclusion

The Stage-1 mock testing successfully verified the feasibility of the selected baseline architecture.

The following seven key functions have passed mock testing:

1. Source encoding and decoding.
2. PN XOR scrambling and descrambling.
3. Repetition-3 channel coding and decoding.
4. Frame construction and parsing.
5. Gray-coded QPSK modulation and demodulation.
6. AWGN fixed-seed reproducibility.
7. Preamble-based synchronization.

The result was:

```text
pytest tests -q
7 passed in 0.24s
```

This confirms that the basic module interfaces are ready for the next stage.

However, the current project is still not the final communication system. The next step is to implement the complete end-to-end chain, generate `received.txt`, generate `metrics.json`, generate required plots, and verify exact file recovery under the required public baseline condition.

---

## 10. Stage-2 End-to-End Verification

After the Stage-1 mock tests passed, the full end-to-end baseline pipeline was implemented and verified.

Validation commands and results:

```text
pytest tests -q: 7 passed
public core module tests: 9 passed
required CLI command ran successfully
```

The required CLI command was:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

End-to-end recovery result:

```text
results/received.txt matched Test.txt at byte level
BER = 0.0
FER = 0.0
text_match_rate = 1.0
checksum_pass = true
```

Generated files:

```text
results/received.txt
results/metrics.json
results/constellation.png
results/ber_curve.png
results/sync_peak.png
```

Low-SNR robustness:

```text
Low-SNR smoke test did not crash.
When recovery fails, the program still writes output and records failure information in metrics.json.
```

Public tests note:

Local `pytest public_tests -q` still has five remaining errors in this Windows execution environment. The errors occur when the public test fixture calls `shutil.rmtree(results)` and Windows denies deletion of `results/ber_curve.png`.

This is a local filesystem permission issue during test cleanup, not a communication-chain recovery failure. The required CLI command runs successfully, and the recovered file matches `Test.txt` at byte level under the baseline SNR = 12 dB, AWGN, seed = 2026 condition.

---

## 11. Level 3 Extension Verification

The Level 3 extension adds a flat Rayleigh fading channel, known-channel simple one-tap equalization, and AWGN-vs-Rayleigh BER comparison plotting.

New tests added:

```text
Rayleigh channel reproducibility test
One-tap equalization sanity test
Rayleigh CLI smoke test
```

Combined local test result:

```text
pytest tests -q
10 passed
```

The original seven Stage-1 mock tests remain included in this result and did not fail.

Baseline AWGN status:

```text
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
AWGN result: results/received.txt matched Test.txt at byte level
BER = 0.0
FER = 0.0
text_match_rate = 1.0
checksum_pass = true
```

Rayleigh smoke result at SNR = 12 dB, seed = 2026:

```text
python main.py --input Test.txt --output results/received_rayleigh.txt --snr 12 --seed 2026 --mod qpsk --channel rayleigh
channel = rayleigh
equalization = one-tap
fading_model = flat_rayleigh
BER = 0.005711488250652741
FER = 1.0
text_match_rate = 0.028985507246376812
checksum_pass = false
failure_reason = utf8_decode_error
```

This Rayleigh result is not treated as an exact recovery result. The extension runs without crashing and records the residual errors honestly. The final AWGN acceptance metrics are stored in `results/metrics.json`, while the Rayleigh extension metrics are also archived in `results/metrics_rayleigh.json`.

Generated plot files include:

```text
constellation.png
ber_curve.png
ber_curve_compare.png
sync_peak.png
```
