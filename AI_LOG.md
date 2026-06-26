# AI Log

## Project Stage Summary

Recorded stages:

- PRD requirement analysis
- `DESIGN.md` drafting
- `TEST_PLAN.md` drafting
- Stage-1 mock skeleton and tests
- `MOCK_TEST_REPORT.md`
- Stage-2 full pipeline implementation
- Metrics and plots generation
- Windows `public_tests` permission issue debugging

Academic integrity statement:

The implementation does not hard-code `Test.txt` content, the expected output,
payload length, seed-specific received text, or synchronization offset. The
program reads the input file dynamically, computes payload bits, frame fields,
CRC32, metrics, and plots from the actual run, and supports variable UTF-8 text
content.

## Prompt 1

Context stage: PRD requirement analysis, `DESIGN.md` drafting, `TEST_PLAN.md`
drafting, and Stage-1 mock skeleton planning.

User prompt: create a minimal testable Python project skeleton based on
`DESIGN.md` and `TEST_PLAN.md`, without implementing the final complete system.

AI-generated content:

- Added `main.py` CLI skeleton.
- Added modular files under `src/`.
- Added `tests/test_mock_stage1.py` with seven mock tests.

Manual changes and review:

- Verified the QPSK Gray mapping manually against the PRD.
- Ran `pytest tests -q` and confirmed the first-stage mock tests passed.

Adoption reason:

- The skeleton matched the documented module boundaries and avoided hard-coded
  `Test.txt` content.

## Prompt 2

Context stage: `MOCK_TEST_REPORT.md` documentation.

User prompt: write a mock test report describing test purpose, environment,
seven mock tests, test result, found issue, design revision, and conclusion.

AI-generated content:

- Added `MOCK_TEST_REPORT.md`.
- Recorded that `main.py` was still a placeholder after Stage 1.
- Recorded the next-stage plan for `received.txt`, `metrics.json`, and plots.

Manual changes and review:

- Checked that the report clearly stated Stage 1 scope and did not claim final
  end-to-end recovery.

Adoption reason:

- The report documents the transition from mock testing to full system
  implementation.

## Prompt 3

Context stage: Stage-2 full pipeline implementation, metrics generation, and
plot generation.

User prompt: implement the complete end-to-end wireless communication file
transmission system without breaking the seven mock tests.

AI-generated content:

- Added `src/pipeline.py`, `src/metrics.py`, `src/plots.py`, and `src/utils.py`.
- Updated `main.py` to run the full chain.
- Generated `results/received.txt`, `results/metrics.json`, and three plots.

Manual changes and review:

- Verified byte-level equality between `Test.txt` and `results/received.txt`.
- Ran `pytest tests -q`.
- Ran the required CLI command at SNR = 12 dB and seed = 2026.

Adoption reason:

- The complete chain produced exact recovery at the baseline condition while
  preserving the Stage 1 unit-test interfaces.

## Prompt 4

Context stage: Windows `public_tests` permission issue debugging.

User prompt: inspect Windows file writing, image saving, and result generation
logic, especially why the `results/` directory cannot be deleted by pytest
fixtures.

AI-generated content:

- Changed plot saving to write Matplotlib figures into an in-memory PNG buffer.
- Closed figures with `plt.close(fig)` and `plt.close("all")`.
- Wrote PNG bytes with `Path.write_bytes`.

Manual changes and review:

- Confirmed that text and JSON outputs use `Path.write_bytes` and
  `Path.write_text`.
- Confirmed no explicit file handle is kept open under `results/`.
- Checked Windows file attributes and ACL information for generated PNG files.

Adoption reason:

- The buffer-based save path minimizes file-handle risk and makes result
  generation easier to reason about on Windows.

## Prompt 5

Context stage: Level 3 Rayleigh fading channel and one-tap equalization
extension.

User prompt: add a Level 3 extension with Rayleigh fading, known-channel
one-tap equalization, comparison experiment support, tests, and documentation
without breaking the AWGN baseline.

AI-generated content:

- Added Rayleigh fading channel and one-tap equalization helpers.
- Added optional `--channel rayleigh` CLI support.
- Added Rayleigh metrics fields including `equalization`, `fading_model`,
  `rayleigh_enabled`, and `channel_estimation`.
- Added `ber_curve_compare.png` generation for AWGN vs Rayleigh comparison.
- Added Level 3 tests for Rayleigh reproducibility, equalization sanity, and
  Rayleigh CLI smoke.
- Kept final AWGN acceptance metrics in `results/metrics.json` and archived
  Rayleigh extension metrics in `results/metrics_rayleigh.json`.
- Added `EXPERIMENT_REPORT.md`.

Manual changes and review:

- Verified that the default AWGN command still recovered `Test.txt` at byte
  level with BER = 0.0.
- Verified that Rayleigh mode runs without crashing and records the actual
  residual errors instead of forcing a correct result.
- Confirmed again that no `Test.txt` content, output text, payload length, or
  seed-specific received result was hard-coded.

Adoption reason:

- The extension adds a more realistic wireless channel experiment while keeping
  the required baseline AWGN system unchanged.
