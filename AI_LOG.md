# AI LOG

## Prompt 1

User prompt: read PRD.docx, README.md, feature file, and public tests; implement the PRD system without hardcoding `Test.txt` or directly copying input to output.

AI generated: project scan, public test interface summary, and a module plan matching the fixed wireless chain.

Manual checkpoint: verified PRD text from docx and confirmed `length` must represent original source payload bits.

## Prompt 2

User prompt: create DESIGN.md, TEST_PLAN.md, MOCK_TEST_REPORT.md, AI_LOG.md, main.py, src/, and tests/.

AI generated: modular Python implementation for source coding, PN scrambling, repetition coding, framing, QPSK, AWGN, synchronization, pipeline, CLI, and documentation drafts.

Manual edited/change notes: kept the communication chain real, added aliases expected by public tests, and avoided any direct `shutil.copy` or input-to-output file copy shortcut.

## Prompt 3

User prompt: run `python -m pytest public_tests -q` and iterate until public tests pass as much as possible.

AI generated: a debugging plan to run public tests, inspect failures, and adjust module interfaces or edge cases.

Adopt reason: the final design is simple enough to explain in an oral defense, matches PRD QPSK/AWGN/sync requirements, and is robust to hidden texts, seeds, and frame offsets.

## Follow-up Debug Plan

Run public tests, then inspect any failures around frame length, QPSK padding, synchronization return shape, metrics fields, and plot generation.

## Prompt 4

User prompt: add a Level 3 Rayleigh flat fading channel and a preamble-based channel estimator/equalizer on the `feature/rayleigh-equalizer` branch, while keeping public tests at 22 passed and avoiding a rewrite.

AI generated: `rayleigh_flat()`, `estimate_flat_channel()`, and `equalize_flat_channel()` in the channel module; a `--channel rayleigh` branch in the pipeline; Rayleigh-specific metrics fields; and `tests/test_rayleigh_equalizer.py`.

Manual edited/change notes: the AWGN function signature and baseline path were intentionally left unchanged. The Rayleigh path was inserted only after channel selection and before QPSK demodulation, using synchronized preamble symbols for least-squares channel estimation.

Verification result: `python -m pytest public_tests -q` reported 22 passed, `python -m pytest tests -q` reported 4 passed, and the Rayleigh CLI command completed with BER 0 and `text_match_rate` 1.0 at SNR 18 dB.

Adopt reason: the extension is small, explainable, and matches the communication model `y = h*x + n`; it demonstrates channel estimation and equalization without destabilizing the required AWGN baseline.
