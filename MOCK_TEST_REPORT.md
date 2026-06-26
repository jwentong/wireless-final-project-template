# Mock Test Report

## Summary

Mock testing was used before final verification to check interfaces, frame structure, synchronization, and end-to-end feasibility. The tests are implemented in `tests/test_wireless_pipeline.py` and complemented by the teacher public tests.

## Mock 1: Source Codec

Prompt / purpose: verify that a Chinese UTF-8 sentence can pass through Source Encode and Source Decode.

Result: the bitstream length is byte-aligned and the decoded text equals the original text.

Design impact: no revision was required for byte ordering, but the design explicitly documents big-endian byte-to-bit conversion.

## Mock 2: Frame Structure

Prompt / purpose: verify that an odd-length payload can be framed and parsed without losing length information.

Initial issue / defect: QPSK padding and channel coding make the transmitted payload length different from the original source payload length. A single length field is not enough internally after channel coding.

Revision / change: the design keeps the PRD payload length semantics and adds an internal `tx_payload_length` field so the receiver can parse the channel-coded payload exactly before channel decoding.

## Mock 3: QPSK Mapping

Prompt / purpose: verify the PRD Gray mapping: `00, 01, 11, 10` map to the four required quadrants.

Result: symbols match the required normalized constellation and noiseless demodulation returns the original bit pairs.

Design impact: no revision was required; the mapping table was copied into `DESIGN.md` to support defense explanation.

## Mock 4: Synchronization

Prompt / purpose: verify that the receiver can detect a preamble after a synthetic symbol prefix.

Initial risk: assuming the receiver knows the frame start would violate the PRD and hidden tests can randomize the prefix.

Revision / change: synchronization now searches all candidate windows with preamble correlation and reports `sync_start_index`, `sync_expected_offset`, and `sync_error_symbols`.

## Mock 5: End-to-End CLI

Prompt / purpose: run the full chain at 12 dB with fixed seed and verify exact text recovery.

Result: the local pipeline test requires `received.txt` to match the input text and `checksum_pass` to be true.

Design impact: metrics and plot generation were integrated into the main pipeline rather than handled by a separate manual script, so the unified CLI produces all required artifacts.

## Remaining Risks

At low SNR, errors may exceed repetition-3 correction capability. The expected behavior is not a crash; the system records BER, FER, text_match_rate, checksum_pass, and failure_reason. This is documented as a controlled failure mode rather than treated as a public-threshold defect.

