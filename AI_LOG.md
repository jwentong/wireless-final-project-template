# AI Usage Log

## Interaction 1

Prompt: Read the wireless communication PRD and identify the required system chain, grading criteria, and high-score strategy.

AI output: Summarized the fixed chain, required files, QPSK/AWGN/synchronization requirements, metrics, plots, and document expectations.

Manual edited/change: The implementation plan was narrowed to a robust baseline with convolutional coding plus Viterbi decoding, PN Scramble, CRC32, QPSK, AWGN, and preamble correlation.

Adoption reason: This design satisfies the public tests and is simple enough to explain during oral defense.

## Interaction 2

Prompt: Inspect the teacher template and public pytest tests, then implement the required module interfaces.

AI output: Located required functions in `src/source.py`, `src/framing.py`, `src/scramble.py`, `src/channel_coding.py`, `src/modulation.py`, `src/channel.py`, and `src/synchronization.py`.

Manual edited/change: Function names were kept close to public-test discovery names so the grader can import them directly.

Adoption reason: Stable interfaces reduce hidden integration risk.

## Interaction 3

Prompt: Generate an end-to-end CLI that produces `received.txt`, `metrics.json`, and result plots without interactive input.

AI output: Created a non-interactive `argparse` entry point with reproducible seed handling and result generation.

Manual edited/change: Metrics and plots were aligned with PRD field names and grading rubrics.

Adoption reason: The CLI is exactly what the teacher workflow runs.

## Interaction 4

Prompt: Run public tests and fix failures.

AI output: Test failures were used to revise parsing, padding, synchronization, and output behavior.

Manual edited/change: Final code changes were accepted only when they preserved the real wireless link and did not directly copy input files to output files.

Adoption reason: This keeps the project academically honest and robust for hidden tests.
