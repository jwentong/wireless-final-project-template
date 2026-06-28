# MOCK_TEST_REPORT

## Mock Cases

- Mock test 1: Source codec round trip passed for ASCII, Chinese, punctuation, and empty
  text.
- Mock test 2: QPSK no-noise modulation/demodulation passed for all Gray-coded symbol pairs.
- Mock test 3: AWGN with fixed seed produced repeatable output.
- Mock test 4: Synchronization passed for random offsets in the PRD range `[0, 128]` at
  12 dB.
- Mock test 5: End-to-end run at 12 dB recovered `Test.txt` exactly.

## Design Adjustments

- Protected the frame header with repetition-3 coding to avoid length/CRC
  corruption from isolated bit errors.
- Added explicit low-SNR failure reporting so metrics are still generated when
  text recovery is imperfect.
- Generated all three requested visualizations instead of only two, because
  they are useful for debugging.

## DESIGN.md Revision Record

- Revision 1: updated the design after mock tests showed that an unprotected
  header is a risk.
- Revision 2: changed the public QPSK API to return a symbol list while keeping
  padding handling inside the pipeline.
- Revision 3: updated the module interface list to match the teacher public
  tests and hidden-test style imports.
- Revision 4: added Level 3 Rayleigh fading, ZF equalization, and convolutional
  Viterbi modules without changing the default public-test command.

## Level 3 Mock Results

- Mock test 6: `--channel rayleigh` completed and wrote metrics with channel
  gain and ZF equalizer fields.
- Mock test 7: convolutional encoder plus Viterbi decoder recovered noiseless
  random bitstreams.
- Mock test 8: the original teacher public tests still passed after the Level 3
  changes, reducing regression risk.
