# Experimental Results and Analysis

## Result Summary

The baseline command is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

For the teacher-provided `Test.txt`, the current result is:

- `received.txt` exactly matches `Test.txt`.
- `ber = 0.0`
- `fer = 0.0`
- `text_match_rate = 1.0`
- `checksum_pass = true`
- `coding_scheme = convolutional(7,5)+viterbi`

## Plot Interpretation

`constellation.png` shows the received QPSK symbols after AWGN. At 12 dB, points cluster around the four normalized Gray-coded constellation points, so hard-decision demodulation is reliable.

`sync_peak.png` shows the matched-correlation output of the pseudo-random preamble. The detected `sync_start_index` matches the simulated random prefix length, which proves the receiver is not assuming the frame start.

`ber_curve.png` shows BER decreasing as SNR increases. Low SNR can still cause bit errors, but the convolutional code and Viterbi decoder improve robustness compared with uncoded hard decisions.

## Failure and Bottleneck Analysis

The first bottleneck at very low SNR is usually QPSK hard-decision demodulation, because noisy samples may cross constellation decision boundaries. A second risk is synchronization: if the preamble correlation peak is not dominant, the receiver may parse the wrong frame start and fail CRC. The pseudo-random preamble was selected to reduce ambiguous correlation peaks. CRC/checksum failure is therefore a useful diagnostic signal: it distinguishes a recovered clean frame from a corrupted or misaligned frame.

