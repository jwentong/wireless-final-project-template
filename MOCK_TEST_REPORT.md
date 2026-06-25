# Mock Test Report

## 1. Test Purpose

The purpose of this mock test stage is to verify that the first-stage wireless
communication project skeleton is feasible and testable before implementing the
complete end-to-end system.

This stage focuses on the core module interfaces described in `DESIGN.md` and
`TEST_PLAN.md`:

- UTF-8 source coding
- PN XOR scrambling
- Repetition-3 channel coding
- Frame build and parse
- Gray-coded QPSK modulation and demodulation
- AWGN channel reproducibility
- Preamble correlation synchronization

The tests intentionally do not verify final `received.txt` generation yet.

## 2. Test Environment

| Item | Value |
|---|---|
| Language | Python 3 |
| Test framework | pytest |
| Main dependency | numpy |
| Test command | `pytest tests -q` |
| Project stage | Stage 1 mock tests |

## 3. Mock Test Coverage

### MOCK-01 Source Encode/Decode Round Trip

This test verifies that mixed UTF-8 text can be converted to big-endian payload
bits and decoded back to exactly the same text. It confirms that the source
codec works on bytes rather than hard-coded text content.

### MOCK-02 Scrambler Reversibility

This test verifies that PN XOR scrambling is reversible when the same seed is
used for scrambling and descrambling.

### MOCK-03 Repetition-3 Encode/Decode

This test verifies that each bit is repeated three times by the encoder and that
the decoder recovers bits using majority voting.

### MOCK-04 Frame Build/Parse

This test verifies that a frame can be built and parsed consistently. It checks
the preamble, payload length field, encoded payload field, and CRC32 checksum.

### MOCK-05 QPSK Mapping/Demapping Without Noise

This test verifies that QPSK follows the required Gray-coded mapping:

```text
00 -> (1+j)/sqrt(2)
01 -> (-1+j)/sqrt(2)
11 -> (-1-j)/sqrt(2)
10 -> (1-j)/sqrt(2)
```

It also verifies that noiseless demodulation recovers the original bits.

### MOCK-06 AWGN Fixed Seed Reproducibility

This test verifies that the AWGN channel produces identical received symbols
when the same input symbols, SNR, and random seed are used.

### MOCK-07 Synchronization With Known Prefix Offset

This test verifies that preamble correlation synchronization can detect a known
symbol prefix offset before the valid QPSK frame.

## 4. Test Result

The mock test command was:

```bash
pytest tests -q
```

Result:

```text
7 passed
```

All seven first-stage mock tests passed.

## 5. Issues Found

The current `main.py` is only a placeholder command-line entry point. It supports
the required argument structure, but it does not yet implement the complete
end-to-end transmission and reception pipeline.

As a result, this stage does not yet generate:

- `results/received.txt`
- `results/metrics.json`
- `results/constellation.png`
- `results/ber_curve.png`
- `results/sync_peak.png`

This is expected for the first-stage skeleton.

## 6. Design Revision

The next development stage should update the implementation to connect the
tested modules into a complete system:

1. Read the input text file and source-encode it.
2. Scramble, repetition-code, frame, and QPSK-modulate the payload.
3. Pass the symbols through AWGN with optional random prefix offset.
4. Synchronize, demodulate, parse, decode, descramble, and source-decode.
5. Write `results/received.txt`.
6. Write `results/metrics.json`.
7. Generate at least two required plots.

This revision keeps the first-stage interface design and adds the next required
end-to-end outputs.

## 7. Conclusion

The basic module interfaces are feasible and testable. The project can now move
from the mock testing stage into the complete wireless communication system
implementation stage.
