# AI_LOG

## Key Prompts

Prompt 1: Read the supplied wireless communication PRD carefully, design the
project implementation flow, generate tests for PRD conformance, and implement
the project code.

Prompt 2: Use the teacher template repository and public tests as the grading
interface. Adapt function names, module boundaries, command-line arguments, and
output files to match the public tests without bypassing the communication
chain.

Prompt 3: Improve the project toward the 85+ target by completing the Level 2
requirements: reversible scrambling, BER-SNR curve, constellation plot,
synchronization peak plot, mock-test report, and design revision record.

Prompt 4: Continue from the 85+ implementation and add 100-point Level 3
modules while preserving teacher public-test compatibility.

Prompt 5: Freeze new feature work and prepare a stable final submission by
cleaning temporary files, correcting README, aligning metrics semantics, and
checking document-code consistency.

## AI Generated Content

- Project structure and documentation files.
- Modular Python implementation for source coding, scrambling, channel coding,
  framing, QPSK, AWGN, synchronization, metrics, plots, and CLI orchestration.
- Public/hidden-style pytest files.

## Manual Engineering Decisions

- Chose repetition-3 coding because it is simple to explain and directly
  demonstrates channel coding and majority decoding.
- Used CRC32 over original UTF-8 bytes for deterministic checksum validation.
- Used dependency-free PNG generation so grading does not depend on matplotlib.
- Preserved the PRD command-line interface exactly.
- Edited public module aliases manually so teacher tests can find
  `source_encode`, `channel_encode`, `parse_frame`, `awgn`, and `synchronize`
  while keeping the internal implementation modular.
- Added optional Rayleigh/ZF and convolutional Viterbi paths as opt-in features
  so the required AWGN public-test path remains stable.
- Corrected metrics so default AWGN runs do not imply Level 3 modules were
  enabled; optional modules are now separated into enabled and available lists.
- Rewrote README from teacher-template wording into a student final-project
  usage guide.

## Debug Record

- PRD extraction initially hit Windows path encoding issues, so the DOCX was
  copied into `work/prd.docx` before extraction.
- Header protection was included after mock-test reasoning showed the header is
  the most fragile part of the frame.
- The first implementation exposed QPSK modulation as `(symbols, padding)`.
  Teacher tests expect a direct symbol list, so the public API was changed and
  padding is now tracked inside the pipeline from the original bit length.

## Final Adoption Reasons

The final version adopts this design because it satisfies the fixed PRD chain,
matches the teacher template public tests, avoids direct file-copy shortcuts,
and remains explainable for oral defense. The extra Level 2 artifacts improve
the expected score ceiling beyond the Level 1 baseline.

The Level 3 additions were adopted because they are standard wireless
communication extensions: fading plus equalization tests channel effects beyond
AWGN, and convolutional coding plus Viterbi demonstrates stronger FEC than a
simple repetition code.

Final cleanup was adopted to reduce submission risk: the public command remains
the base link, generated metrics describe the actual run, and cache/smoke-output
folders are excluded from submission.
