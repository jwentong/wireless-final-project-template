# Wireless Communication File Transfer Baseband Simulation Design

## 1. Goal and Fixed Chain

This project implements the PRD fixed end-to-end chain:

`Test.txt -> Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Decrypt/Descramble -> Source Decode -> received.txt -> Metrics/Plots`.

The baseline system uses Gray-coded QPSK, an AWGN channel, a preamble-based Synchronization module, reversible Scramble processing, convolutional Channel Encode / Viterbi Channel Decode, and metrics output for BER, FER, text recovery, checksum, seed, SNR, and frame start. The convolutional code is also the Level3 improvement module selected from the PRD options.

## 2. Module Interfaces

- Source Encode: `source_encode(text) -> list[int]`. UTF-8 text is converted to bytes and then to a bit stream in most-significant-bit order.
- Source Decode: `source_decode(bits) -> str`. Bits are grouped into bytes and decoded as UTF-8 after the frame length removes padding.
- Encrypt/Scramble: `scramble(bits, seed) -> list[int]` and `descramble(bits, seed) -> list[int]`. A reproducible PN sequence is generated from `seed`; XOR makes the operation reversible.
- Channel Encode: `channel_encode(bits) -> list[int]`. A rate-1/2 convolutional encoder with constraint length 3 and generator polynomials `(7,5)` appends two zero tail bits to terminate the trellis.
- Channel Decode: `channel_decode(bits) -> list[int]`. A hard-decision Viterbi decoder finds the minimum-Hamming-distance trellis path and removes the two termination bits.
- Frame Build: `build_frame(payload_bits) -> list[int]`. The frame contains preamble, a 32-bit original source length field, a 32-bit encoded payload length field, encoded payload bits, and CRC32 over the original payload bytes.
- Frame Parse: `parse_frame(frame_bits) -> dict`. It checks preamble if present, reads both length fields, removes QPSK padding, and returns the encoded payload bits for Viterbi decoding.
- QPSK Modulate: `qpsk_modulate(bits) -> np.ndarray`. If the input bit count is odd, one zero is padded at the end.
- QPSK Demodulate: `qpsk_demodulate(symbols) -> list[int]`. Hard decision by quadrant recovers Gray-coded bit pairs.
- Channel: `awgn(symbols, snr_db, seed) -> np.ndarray`. SNR is defined as average received symbol power divided by average complex Gaussian noise power.
- Synchronization: `synchronize(received, preamble) -> dict`. Correlation with the known preamble finds the frame start without assuming the receiver knows the offset.

## 3. Frame Structure

The serialized bit frame is:

`preamble_bits | original_length_32 | encoded_payload_length_32 | encoded_payload_bits | crc_32`

`original_length_32` records the source payload bit count after Source Encode and before Scramble. `encoded_payload_length_32` records the exact number of encoded bits inside the frame, so the receiver can separate payload from CRC even when QPSK padding adds one zero at the end. The CRC/checksum covers the original payload bytes. `metrics.json` records `checksum_pass` and `crc_pass` after Viterbi decoding and descrambling.

The preamble uses a fixed pseudo-random QPSK-friendly bit pattern. After modulation it provides a sharp correlation peak for Synchronization and avoids the ambiguous side peaks that can occur with a short repeated pattern. The receiver can handle random leading offsets because it first detects the preamble, then demodulates from that detected symbol index.

## 4. QPSK Mapping and Normalization

The baseline QPSK mapper follows the PRD Gray mapping:

- `00 -> (1+j)/sqrt(2)`
- `01 -> (-1+j)/sqrt(2)`
- `11 -> (-1-j)/sqrt(2)`
- `10 -> (1-j)/sqrt(2)`

The `1/sqrt(2)` normalization keeps the average symbol power close to 1. This makes the AWGN SNR definition direct and repeatable.

## 5. Metrics and Plots

The CLI writes `results/received.txt`, `results/metrics.json`, `results/constellation.png`, `results/ber_curve.png`, and `results/sync_peak.png`.

Important metrics include `snr_db`, `seed`, `modulation`, `channel`, `payload_bits`, `ber`, `fer`, `text_match_rate`, `checksum_pass`, and `sync_start_index`. BER is computed on the original source payload bits after the full receive chain. FER is 0 when CRC passes and 1 otherwise.

## 6. Expected Results and Failure Analysis

At SNR >= 12 dB in AWGN with fixed seed, Viterbi decoding and a clear preamble should recover `received.txt` exactly, so BER is expected to be 0 and `text_match_rate` is 1.0. At lower SNR, noise can first damage QPSK hard decisions or reduce the Synchronization correlation peak. If the frame start is wrong, length and CRC fail quickly; if only a few data symbols are wrong, Viterbi decoding can correct many isolated errors, otherwise BER and FER rise. The BER-SNR curve should decrease as SNR increases, and the QPSK constellation should cluster more tightly around the four normalized points at high SNR.
