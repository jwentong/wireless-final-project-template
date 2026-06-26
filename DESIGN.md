# DESIGN

## Fixed System Chain

The implemented base system follows the required chain:

`Test.txt -> Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Decrypt/Descramble -> Source Decode -> received.txt -> Metrics/Plots`

## Module Choices

- Source Encode / Source Decode: UTF-8 text is converted byte by byte to an 8-bit bitstream and reconstructed from complete bytes.
- Encrypt/Scramble: a reproducible PN sequence generated from `seed` is XORed with payload bits. The same function is used for descrambling.
- Channel Encode / Channel Decode: a rate 1/3 repetition code repeats every bit three times; the receiver uses majority decision.
- Frame Build: the serialized frame is `preamble | length | payload | checksum`. The `length` field is 32 bits and records the original source payload bit count before scrambling. In the main chain the frame payload is the channel-coded scrambled payload, so the receiver reads `length * 3` payload bits before the checksum. The checksum is CRC32 over the original source payload bitstream.
- QPSK Modulate / QPSK Demodulate: Gray mapping is fixed as `00 -> (1+j)/sqrt(2)`, `01 -> (-1+j)/sqrt(2)`, `11 -> (-1-j)/sqrt(2)`, `10 -> (1-j)/sqrt(2)`. Odd-length input to QPSK is padded with one zero at the frame tail; frame parsing uses `length` to ignore padding.
- Channel: AWGN uses SNR as average QPSK symbol power divided by complex Gaussian noise power. Fixed `seed` makes noise reproducible.
- Synchronization: the receiver correlates received symbols with known QPSK preamble symbols and reports `sync_start_index`.
- Metrics/Plots: `metrics.json` records SNR, seed, modulation, channel, payload_bits, BER, FER, text_match_rate, checksum_pass, and sync_start_index. Plots include QPSK constellation, synchronization peak, and BER-SNR curve.

## Result Interpretation

At SNR 12 dB, QPSK constellation points should cluster around four unit-power Gray-coded ideal points. BER and `text_match_rate` improve as SNR increases because hard QPSK decisions cross quadrant boundaries less often. A failure can come from noise-induced symbol decision errors, a wrong synchronization peak, a corrupted length field, or checksum mismatch after channel decoding.

## Level 3 Rayleigh Flat Fading and Equalizer

The Level 3 extension adds an optional Rayleigh flat fading channel while keeping the AWGN baseline command and behavior compatible. When `--channel awgn` is used, the original AWGN-only base chain is still used.

For `--channel rayleigh`, the channel model is:

`y = h * x + n`

Here `x` is the transmitted QPSK symbol sequence, `h` is one fixed complex Gaussian fading coefficient for the whole frame, and `n` is complex AWGN. The coefficient `h` is generated from the configured random `seed`, so repeated runs are reproducible.

After synchronization, the receiver extracts the received preamble symbols and compares them with the known QPSK preamble symbols. The flat channel is estimated with a least-squares preamble estimator:

`h_hat = sum(y_preamble * conj(x_preamble)) / sum(abs(x_preamble)^2)`

The synchronized frame is then equalized before QPSK demodulation:

`x_equalized = y / h_hat`

The implementation guards against an extremely small `h_hat` to avoid division-by-zero failures. Rayleigh-mode metrics additionally record `equalizer`, `channel_estimation`, `estimated_channel_real`, `estimated_channel_imag`, and `rayleigh_fading`.
