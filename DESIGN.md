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

