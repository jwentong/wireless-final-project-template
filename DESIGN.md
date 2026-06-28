# DESIGN

## Implementation Flow

Fixed PRD chain:

```text
Test.txt -> Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build
-> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate
-> Channel Decode -> Decrypt/Descramble -> Source Decode -> received.txt
-> Metrics/Plots
```

1. Read `Test.txt` as UTF-8 text.
2. Convert text bytes to a payload bitstream.
3. Scramble payload bits with a deterministic PN/XOR stream derived from
   `seed`.
4. Apply a repetition-3 channel code to payload bits.
5. Build a frame with:
   - 128-bit deterministic preamble for synchronization.
   - Repetition-3 protected 64-bit header.
   - Header fields: original payload bit length and CRC32 of original bytes.
   - Encoded scrambled payload.
6. Modulate all frame bits with required Gray-coded QPSK:
   - `00 -> (1+j)/sqrt(2)`
   - `01 -> (-1+j)/sqrt(2)`
   - `11 -> (-1-j)/sqrt(2)`
   - `10 -> (1-j)/sqrt(2)`
7. Add a random 0-128 QPSK-symbol timing offset and AWGN.
8. Detect the frame start by correlating received symbols with the known
   preamble symbols.
9. QPSK demodulate from the detected start.
10. Parse and protectively decode the frame header.
11. Decode repetition-3 payload bits.
12. Descramble bits, trim to the header length, decode UTF-8, and write
    `results/received.txt`.
13. Write `results/metrics.json` and plots.

## Module Interfaces

- `src.source`: UTF-8 text/bytes to bitstream conversion and inverse.
- `src.scrambler`: reversible PN/XOR scrambling.
- `src.channel_code`: repetition-3 encoder and majority-vote decoder.
- `src.convolutional`: optional rate-1/2 convolutional code and hard-decision
  Viterbi decoder for Level 3 experiments.
- `src.frame`: preamble generation, frame build, sync correlation, frame parse.
- `src.modulation`: QPSK modulation/demodulation using PRD Gray mapping.
- `src.channel`: AWGN channel, optional flat Rayleigh fading, deterministic
  random timing offset, channel estimation, and ZF equalization.
- `src.metrics`: BER, text match rate, metrics JSON assembly.
- `src.plots`: dependency-free PNG plot generation.
- `src.pipeline`: end-to-end orchestration used by `main.py`.

## Key Parameters

- Modulation: QPSK only for the base path.
- Channel: AWGN only for the base path.
- Optional channel: flat Rayleigh fading with a single complex channel gain per
  frame. Receiver estimates the gain from the known preamble and applies ZF
  equalization before QPSK demodulation.
- SNR definition: average QPSK symbol power divided by complex AWGN noise
  power, in dB.
- Synchronization offset: random integer in `[0, 128]` QPSK symbols.
- Channel coding: repetition-3, code rate 1/3.
- Optional FEC: rate-1/2 convolutional code with generator polynomials
  `111` and `101`, decoded by hard-decision Viterbi.
- Header protection: repetition-3 over 32-bit payload length and 32-bit CRC32.
- Checksum: CRC32 over original UTF-8 payload bytes.

## Expected Risks And Mitigations

- Header bit errors can corrupt payload length. Mitigation: repetition-3 header
  protection and bounded parse logic.
- Low SNR can cause UTF-8 decode errors. Mitigation: decode with replacement
  and report `checksum_pass=false`, `fer=1.0`, and reduced match rate instead
  of crashing.
- Synchronization ambiguity can occur when noise is high. Mitigation: use a
  128-bit preamble and report both detected and true offsets in metrics.

## Result Interpretation

At SNR = 12 dB under AWGN, the expected public-test result is
`ber=0`, `fer=0`, `text_match_rate=1.0`, and `checksum_pass=true`. The QPSK
constellation should cluster near the four normalized Gray-coded points. The
BER-SNR curve should decrease as SNR increases. The synchronization peak plot
should show a clear maximum at the detected frame start. If SNR is reduced,
noise first affects QPSK demodulation and then repetition decoding; this appears
as nonzero BER, checksum failure, and a lower text match rate.

## Level 3 Enhancement Modules

The base command remains PRD-compatible. For the 100-point target, the
implementation also supports optional higher-level experiments:

```bash
python main.py --input Test.txt --output results/received_rayleigh.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh
python main.py --input Test.txt --output results/received_conv.txt --snr 12 --seed 2026 --mod qpsk --channel awgn --fec conv
```

Rayleigh mode multiplies all frame symbols by one complex fading coefficient,
adds AWGN, then estimates the coefficient from the preamble and applies
zero-forcing equalization. Convolutional mode replaces repetition coding with a
rate-1/2 code and Viterbi decoding. Metrics use `level3_modules` for modules
enabled in the current run and `available_level3_modules` for optional modules
implemented by the project. Therefore the default AWGN + repetition-3 run has
`level3_modules=[]`, while Rayleigh mode records Rayleigh/ZF and convolutional
mode records convolutional Viterbi.

## Design Revision From Mock Tests

Initial design used an unprotected header. Mock tests showed that a single
header bit error can produce an invalid payload length even when most payload
bits recover. The final design repetition-encodes the 64-bit header before
framing, then majority-decodes it before extracting the payload.
